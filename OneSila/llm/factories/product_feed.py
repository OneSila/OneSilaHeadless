from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Sequence

from django.conf import settings
from django.utils import timezone

from llm.exceptions import (
    ProductFeedConfigurationError,
    ProductFeedValidationError,
)
from llm.models import ChatGptProductFeedConfig
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation
from properties.models import ProductProperty
from sales_channels.models import SalesChannelViewAssign


@dataclass(frozen=True)
class _CustomVariant:
    category: Optional[str] = None
    option: Optional[str] = None


class ProductFeedPayloadFactory:
    """Build payloads for the GPT product feed."""

    def __init__(self, *, sales_channel_view_assign: SalesChannelViewAssign):
        self.sales_channel_view_assign = sales_channel_view_assign
        self.sales_channel = sales_channel_view_assign.sales_channel
        if not getattr(self.sales_channel, "gpt_enable", False):
            raise ProductFeedConfigurationError("GPT feed is disabled for this sales channel.")

        self.parent_product = sales_channel_view_assign.product
        self.language_code = self._resolve_language_code()
        self.config = self._load_config()
        self.configurator_items = self._load_configurator_items()
        self.configurator_property_ids = [item.property_id for item in self.configurator_items]

    def build(self) -> List[Dict[str, object]]:
        products = self._resolve_products()
        property_cache = self._prepare_property_cache(products=products)
        translations_map = self._prepare_translations(products=products)
        media_map = self._prepare_media(products=products)
        parent_translation = self._select_translation(
            translations=translations_map.get(self.parent_product.id, [])
        )

        payloads: List[Dict[str, object]] = []
        for product in products:
            translation = self._select_translation(translations=translations_map.get(product.id, []))
            payloads.append(
                self._build_payload_for_product(
                    product=product,
                    translation=translation,
                    parent_translation=parent_translation,
                    property_cache=property_cache,
                    media_map=media_map,
                )
            )

        return payloads

    def _resolve_language_code(self) -> str:
        company = getattr(self.sales_channel, "multi_tenant_company", None)
        if company and getattr(company, "language", None):
            return company.language
        return settings.LANGUAGE_CODE

    def _load_config(self) -> ChatGptProductFeedConfig:
        try:
            return (
                ChatGptProductFeedConfig.objects.select_related(
                    "condition_property",
                    "brand_property",
                    "material_property",
                    "mpn_property",
                    "length_property",
                    "width_property",
                    "height_property",
                    "weight_property",
                    "age_group_property",
                    "expiration_date_property",
                    "pickup_method_property",
                    "color_property",
                    "size_property",
                    "size_system_property",
                    "gender_property",
                    "popularity_score_property",
                    "warning_property",
                    "age_restriction_property",
                    "condtion_new_value",
                    "condtion_refurbished_value",
                    "condtion_usd_value",
                    "age_group_newborn_value",
                    "age_group_infant_value",
                    "age_group_todler_value",
                    "age_group_kids_value",
                    "age_group_adult_value",
                    "pickup_method_in_store_value",
                    "pickup_method_reserve_value",
                    "pickup_method_not_supported_value",
                )
                .get(multi_tenant_company=self.sales_channel.multi_tenant_company)
            )
        except ChatGptProductFeedConfig.DoesNotExist as exc:
            raise ProductFeedConfigurationError("Missing GPT product feed configuration for company.") from exc

    def _load_configurator_items(self) -> List[object]:
        if not self.parent_product.is_configurable():
            return []

        return list(
            self.parent_product
            .get_configurator_properties(public_information_only=False)
            .select_related("property")
            .order_by("sort_order", "id")
        )

    def _resolve_products(self) -> List[Product]:
        if not self.parent_product.is_configurable():
            return [self.parent_product]

        variations = list(self.parent_product.get_configurable_variations(active_only=True))
        if not variations:
            raise ProductFeedValidationError("Configurable product has no active variations to sync.")
        return variations

    def _collect_property_ids(self) -> List[int]:
        property_ids = {
            self.config.condition_property_id,
            self.config.brand_property_id,
            self.config.material_property_id,
            self.config.mpn_property_id,
            self.config.length_property_id,
            self.config.width_property_id,
            self.config.height_property_id,
            self.config.weight_property_id,
            self.config.age_group_property_id,
            self.config.expiration_date_property_id,
            self.config.pickup_method_property_id,
            self.config.color_property_id,
            self.config.size_property_id,
            self.config.size_system_property_id,
            self.config.gender_property_id,
            self.config.popularity_score_property_id,
            self.config.warning_property_id,
            self.config.age_restriction_property_id,
        }
        property_ids.update(self.configurator_property_ids)
        property_ids.discard(None)
        return list(property_ids)

    def _prepare_property_cache(self, *, products: Sequence[Product]) -> Dict[tuple[int, int], ProductProperty]:
        property_ids = self._collect_property_ids()
        if not property_ids:
            return {}

        product_ids = {product.id for product in products}
        if self.parent_product.is_configurable():
            product_ids.add(self.parent_product.id)

        queryset = (
            ProductProperty.objects.filter(
                product_id__in=product_ids,
                property_id__in=property_ids,
            )
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select")
        )

        return {(item.product_id, item.property_id): item for item in queryset}

    def _prepare_translations(self, *, products: Sequence[Product]) -> Dict[int, List[ProductTranslation]]:
        product_ids = {product.id for product in products}
        product_ids.add(self.parent_product.id)

        queryset = ProductTranslation.objects.filter(product_id__in=product_ids)
        translations_map: Dict[int, List[ProductTranslation]] = defaultdict(list)
        for translation in queryset:
            translations_map[translation.product_id].append(translation)
        return translations_map

    def _prepare_media(self, *, products: Sequence[Product]) -> Dict[int, Dict[str, List[MediaProductThrough]]]:
        product_ids = {product.id for product in products}
        if self.parent_product.id not in product_ids:
            product_ids.add(self.parent_product.id)

        assignments = (
            MediaProductThrough.objects.filter(
                product_id__in=product_ids,
                media__type__in=[Media.IMAGE, Media.VIDEO],
                sales_channel__in=[None, self.sales_channel],
            )
            .select_related("media", "sales_channel")
            .order_by("product_id", "sales_channel__isnull", "sort_order", "id")
        )

        grouped: Dict[int, Dict[str, List[MediaProductThrough]]] = defaultdict(lambda: {"channel": [], "default": []})
        for assignment in assignments:
            key = "channel" if assignment.sales_channel_id == self.sales_channel.id else "default"
            grouped[assignment.product_id][key].append(assignment)
        return grouped

    def _select_translation(self, *, translations: Iterable[ProductTranslation]) -> Optional[ProductTranslation]:
        translations = list(translations)
        if not translations:
            return None

        def _match(*, prefer_channel: Optional[int], prefer_language: Optional[str]) -> Optional[ProductTranslation]:
            for trans in translations:
                if prefer_language and trans.language != prefer_language:
                    continue
                if prefer_channel is None and trans.sales_channel_id is not None:
                    continue
                if prefer_channel is not None and trans.sales_channel_id != prefer_channel:
                    continue
                return trans
            return None

        channel_id = getattr(self.sales_channel, "id", None)
        language = self.language_code

        return (
            _match(prefer_channel=channel_id, prefer_language=language)
            or _match(prefer_channel=None, prefer_language=language)
            or _match(prefer_channel=channel_id, prefer_language=None)
            or _match(prefer_channel=None, prefer_language=None)
            or translations[0]
        )

    def _get_property_value(
        self,
        *,
        product: Product,
        property_id: Optional[int],
        property_cache: Dict[tuple[int, int], ProductProperty],
        allow_multiple: bool = False,
    ) -> Optional[object]:
        if not property_id:
            return None
        product_property = property_cache.get((product.id, property_id))
        if not product_property:
            return None
        value = product_property.get_serialised_value(language=self.language_code)
        if isinstance(value, list) and not allow_multiple:
            return value[0] if value else None
        return value

    def _stringify(self, *, value: Optional[object]) -> Optional[str]:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item not in (None, "")) or None
        return str(value)

    def _format_decimal(self, *, value: Optional[Decimal]) -> Optional[str]:
        if value is None:
            return None
        return f"{value:.2f}"

    def _compute_condition(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> str:
        product_property = property_cache.get((product.id, self.config.condition_property_id))
        select_id = getattr(product_property, "value_select_id", None)

        mapping = {
            getattr(self.config.condtion_new_value, "id", None): "new",
            getattr(self.config.condtion_refurbished_value, "id", None): "refurbished",
            getattr(self.config.condtion_usd_value, "id", None): "used",
        }

        return mapping.get(select_id, "new")

    def _compute_age_group(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> Optional[str]:
        product_property = property_cache.get((product.id, self.config.age_group_property_id))
        if not product_property or not product_property.value_select_id:
            return None

        mapping = {
            getattr(self.config.age_group_newborn_value, "id", None): "newborn",
            getattr(self.config.age_group_infant_value, "id", None): "infant",
            getattr(self.config.age_group_todler_value, "id", None): "toddler",
            getattr(self.config.age_group_kids_value, "id", None): "kids",
            getattr(self.config.age_group_adult_value, "id", None): "adult",
        }
        return mapping.get(product_property.value_select_id)

    def _compute_pickup_method(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> Optional[str]:
        product_property = property_cache.get((product.id, self.config.pickup_method_property_id))
        if not product_property or not product_property.value_select_id:
            return None

        mapping = {
            getattr(self.config.pickup_method_in_store_value, "id", None): "in_store",
            getattr(self.config.pickup_method_reserve_value, "id", None): "reserve",
            getattr(self.config.pickup_method_not_supported_value, "id", None): "not_supported",
        }
        return mapping.get(product_property.value_select_id)

    def _compute_dimensions(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> Optional[str]:
        length = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.length_property_id,
                property_cache=property_cache,
            )
        )
        width = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.width_property_id,
                property_cache=property_cache,
            )
        )
        height = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.height_property_id,
                property_cache=property_cache,
            )
        )
        unit = (self.config.length_unit or "").strip()

        if all([length, width, height]) and unit:
            return f"{length}x{width}x{height} {unit}"
        return None

    def _compute_weight(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> Optional[str]:
        weight = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.weight_property_id,
                property_cache=property_cache,
            )
        )
        if not weight:
            return None
        unit = (self.config.weight_unit or "").strip()
        return f"{weight} {unit}".strip()

    def _compute_availability(self, *, product: Product) -> tuple[str, Optional[str]]:
        if product.active:
            return "in_stock", None
        if getattr(product, "allow_backorder", False):
            today = timezone.now().date().isoformat()
            return "preorder", today
        return "out_of_stock", None

    def _build_custom_variants(
        self,
        *,
        product: Product,
        property_cache: Dict[tuple[int, int], ProductProperty],
    ) -> List[_CustomVariant]:
        if not self.configurator_items:
            return [_CustomVariant(), _CustomVariant(), _CustomVariant()]

        color_property_id = self.config.color_property_id
        size_property_id = self.config.size_property_id

        total = len(self.configurator_items)
        has_standard = int(any(item.property_id == color_property_id for item in self.configurator_items)) + int(
            any(item.property_id == size_property_id for item in self.configurator_items)
        )
        extra_items = [
            item for item in self.configurator_items if item.property_id not in {color_property_id, size_property_id}
        ]

        if has_standard:
            if total > 5 or len(extra_items) > 3:
                raise ProductFeedValidationError("Configurable product exposes too many configurable attributes.")
        else:
            if total > 3:
                raise ProductFeedValidationError("Configurable product exposes too many configurable attributes.")

        variants: List[_CustomVariant] = []
        for item in extra_items[:3]:
            value = self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=item.property_id,
                    property_cache=property_cache,
                )
            )
            variants.append(_CustomVariant(category=item.property.name, option=value))

        while len(variants) < 3:
            variants.append(_CustomVariant())
        return variants

    def _extract_media_urls(
        self,
        *,
        assignments: Dict[str, List[MediaProductThrough]],
    ) -> tuple[Optional[str], List[str], Optional[str]]:
        selected = assignments.get("channel") or assignments.get("default") or []
        images = [item for item in selected if item.media.type == Media.IMAGE]
        videos = [item for item in selected if item.media.type == Media.VIDEO]

        thumbnail = None
        additional: List[str] = []

        if images:
            sorted_images = sorted(images, key=lambda item: (not item.is_main_image, item.sort_order, item.id))
            primary = sorted_images[0]
            thumbnail = primary.media.onesila_thumbnail_url()
            additional = [img.media.image_url() for img in sorted_images[1:] if img.media.image_url()]

        video_url = None
        if videos:
            sorted_videos = sorted(videos, key=lambda item: (item.sort_order, item.id))
            for video in sorted_videos:
                video_url = video.media.video_url
                if video_url:
                    break

        return thumbnail, additional, video_url

    def _build_payload_for_product(
        self,
        *,
        product: Product,
        translation: Optional[ProductTranslation],
        parent_translation: Optional[ProductTranslation],
        property_cache: Dict[tuple[int, int], ProductProperty],
        media_map: Dict[int, Dict[str, List[MediaProductThrough]]],
    ) -> Dict[str, object]:
        title = translation.name if translation else product.name
        description = translation.description if translation else None

        assignments = media_map.get(product.id) or media_map.get(self.parent_product.id, {})
        thumbnail, additional_images, video_link = self._extract_media_urls(assignments=assignments)

        link = (
            self.sales_channel_view_assign.remote_url
            if product.id == self.sales_channel_view_assign.product_id
            else SalesChannelViewAssign(
                product=product,
                sales_channel_view=self.sales_channel_view_assign.sales_channel_view,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel_view_assign.multi_tenant_company,
            ).remote_url
        )

        condition = self._compute_condition(product=product, property_cache=property_cache)
        age_group = self._compute_age_group(product=product, property_cache=property_cache)
        pickup_method = self._compute_pickup_method(product=product, property_cache=property_cache)
        dimensions = self._compute_dimensions(product=product, property_cache=property_cache)
        weight = self._compute_weight(product=product, property_cache=property_cache)

        availability, availability_date = self._compute_availability(product=product)
        price, sale_price = product.get_price_for_sales_channel(self.sales_channel)

        item_group_id = None
        item_group_title = None
        if self.parent_product.is_configurable():
            item_group_id = self.parent_product.sku
            if parent_translation:
                item_group_title = parent_translation.name
            else:
                item_group_title = self.parent_product.name

        variants = self._build_custom_variants(product=product, property_cache=property_cache)

        color = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.color_property_id,
                property_cache=property_cache,
            )
        )
        size = self._stringify(
            value=self._get_property_value(
                product=product,
                property_id=self.config.size_property_id,
                property_cache=property_cache,
            )
        )

        payload = {
            "enable_search": bool(self.sales_channel.gpt_enable),
            "enable_checkout": bool(self.sales_channel.gpt_enable_checkout),
            "id": product.sku,
            "gtin": product.ean_code,
            "mpn": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.mpn_property_id,
                    property_cache=property_cache,
                )
            ),
            "title": title,
            "description": description,
            "link": link,
            "condition": condition,
            "product_category": getattr(product.get_product_rule(), "value", None),
            "brand": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.brand_property_id,
                    property_cache=property_cache,
                )
            ),
            "material": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.material_property_id,
                    property_cache=property_cache,
                )
            ),
            "length": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.length_property_id,
                    property_cache=property_cache,
                )
            ),
            "width": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.width_property_id,
                    property_cache=property_cache,
                )
            ),
            "height": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.height_property_id,
                    property_cache=property_cache,
                )
            ),
            "weight": weight,
            "dimensions": dimensions,
            "age_group": age_group,
            "image_link": thumbnail,
            "additional_image_link": additional_images,
            "video_link": video_link,
            "price": self._format_decimal(value=price),
            "sale_price": self._format_decimal(value=sale_price),
            "availability": availability,
            "availability_date": availability_date,
            "inventory_quantity": self.sales_channel.starting_stock or 1,
            "expiration_date": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.expiration_date_property_id,
                    property_cache=property_cache,
                )
            ),
            "pickup_method": pickup_method,
            "item_group_id": item_group_id,
            "item_group_title": item_group_title,
            "color": color,
            "size": size,
            "size_system": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.size_system_property_id,
                    property_cache=property_cache,
                )
            ),
            "gender": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.gender_property_id,
                    property_cache=property_cache,
                )
            ),
            "offer_id": "-".join(
                filter(
                    None,
                    [
                        product.sku,
                        self.sales_channel.gpt_seller_name,
                        self._format_decimal(value=price) or "0.00",
                    ],
                )
            ),
            "custom_variant1_category": variants[0].category,
            "custom_variant1_option": variants[0].option,
            "custom_variant2_category": variants[1].category,
            "custom_variant2_option": variants[1].option,
            "custom_variant3_category": variants[2].category,
            "custom_variant3_option": variants[2].option,
            "seller_name": self.sales_channel.gpt_seller_name,
            "seller_url": self.sales_channel.gpt_seller_url or self.sales_channel.hostname,
            "seller_privacy_policy": self.sales_channel.gpt_seller_privacy_policy,
            "seller_tos": self.sales_channel.gpt_seller_tos,
            "return_policy": self.sales_channel.gpt_return_policy,
            "return_window": self.sales_channel.gpt_return_window,
            "popularity_score": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.popularity_score_property_id,
                    property_cache=property_cache,
                )
            ),
            "warning": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.warning_property_id,
                    property_cache=property_cache,
                )
            ),
            "age_restriction": self._stringify(
                value=self._get_property_value(
                    product=product,
                    property_id=self.config.age_restriction_property_id,
                    property_cache=property_cache,
                )
            ),
        }

        return payload
