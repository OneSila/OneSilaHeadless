from __future__ import annotations

import inspect
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from datetime import date, datetime
from typing import Any

from django.db import transaction

from eancodes.models import EanCode
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation
from properties.models import ProductProperty
from sales_channels.exceptions import MiraklPayloadValidationError, MissingMappingError, PreFlightCheckError
from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductDeleteFactory,
    RemoteProductSyncFactory,
)
from sales_channels.helpers import _content_is_empty, build_content_data
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklPublicDefinition,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
)
from sales_channels.integrations.mirakl.utils.type_parameters import get_mirakl_type_parameter_value
from sales_channels.models import SalesChannelFeedItem, SalesChannelIntegrationPricelist
from sales_prices.models import SalesPriceListItem


class MiraklProductPayloadBuilder:
    _UNSET = object()

    OFFER_FIELD_KEYS = [
        "sku",
        "product-id",
        "product-id-type",
        "description",
        "internal-description",
        "price",
        "price-additional-info",
        "quantity",
        "min-quantity-alert",
        "state",
        "available-start-date",
        "available-end-date",
        "logistic-class",
        "discount-price",
        "discount-start-date",
        "discount-end-date",
        "leadtime-to-ship",
        "update-delete",
    ]

    def __init__(self, *, remote_product, sales_channel_view=None, action: str = SalesChannelFeedItem.ACTION_UPDATE) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.local_product = remote_product.local_instance
        self.sales_channel_view = sales_channel_view
        self.action = action
        self.language = getattr(self.sales_channel.multi_tenant_company, "language", None)
        self._category_cache: dict[str, MiraklCategory | None] = {}
        self._product_type_cache: dict[tuple[int | None, int | None], MiraklProductType | None] = {}
        self._public_definition_cache: dict[str, MiraklPublicDefinition | None] = {}
        self._condition_property_cache: MiraklProperty | None | object = self._UNSET

    def build(self) -> tuple[MiraklProductType, list[dict[str, str]]]:
        if self.local_product is None:
            raise PreFlightCheckError("Mirakl remote product has no linked local product.")

        products = self._resolve_products()
        if not products:
            raise PreFlightCheckError(
                f"Mirakl product {getattr(self.local_product, 'sku', self.local_product.id)} has no rows to push."
            )

        lookup_products = self._get_lookup_products(products=products)
        translations = self._load_translations(products=lookup_products)
        product_properties_by_product = self._load_properties(products=products)
        prices_by_product = self._load_prices(products=products)
        media_by_product = self._load_media(products=lookup_products)
        eans_by_product = self._load_eans(products=products)

        resolved_product_type: MiraklProductType | None = None
        rows: list[dict[str, str]] = []
        for product in products:
            content_product = self._get_content_source_product(product=product)
            product_context = self._build_product_context(
                product=product,
                translation=self._select_translation(translations=translations.get(content_product.id, [])),
                product_properties=list(product_properties_by_product.get(product.id, [])),
                prices=list(prices_by_product.get(product.id, [])),
                images=list(media_by_product.get(content_product.id, [])),
                ean=eans_by_product.get(product.id, ""),
                content_product=content_product,
            )
            product_type = product_context["product_type"]
            if resolved_product_type is None:
                resolved_product_type = product_type
            elif resolved_product_type.id != product_type.id:
                raise PreFlightCheckError(
                    f"Mirakl payload for {getattr(self.local_product, 'sku', self.local_product.id)} spans multiple product types."
                )

            row = self._build_row(product_context=product_context)
            rows.append(row)

        if resolved_product_type is None:
            raise MissingMappingError(
                f"Mirakl product type could not be resolved for {getattr(self.local_product, 'sku', self.local_product.id)}."
            )
        return resolved_product_type, rows

    def _resolve_products(self) -> list[Product]:
        if self.local_product is None:
            return []
        if not self.local_product.is_configurable():
            return [self.local_product]
        return list(self.local_product.get_configurable_variations(active_only=False))

    def _get_lookup_products(self, *, products: list[Product]) -> list[Product]:
        if self.local_product is None or not self.local_product.is_configurable():
            return products
        by_id = {product.id: product for product in products}
        by_id[self.local_product.id] = self.local_product
        return list(by_id.values())

    def _get_content_source_product(self, *, product: Product) -> Product:
        if self.local_product is not None and self.local_product.is_configurable():
            return self.local_product
        return product

    def _build_product_context(
        self,
        *,
        product: Product,
        translation: ProductTranslation | None,
        product_properties: list[ProductProperty],
        prices: list[dict[str, Any]],
        images: list[dict[str, Any]],
        ean: str,
        content_product: Product,
    ) -> dict[str, Any]:
        product_type = self._resolve_product_type(product=product)
        if product_type is None:
            raise MissingMappingError(
                f"Map product {getattr(product, 'sku', product.id)} to a Mirakl category or product type before pushing."
            )

        property_by_id = {item.property_id: item for item in product_properties}
        remote_select_lookup = {
            (value.remote_property_id, value.local_instance_id): value
            for value in MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property__sales_channel=self.sales_channel,
                remote_property__local_instance_id__in=list(property_by_id.keys()),
                local_instance__isnull=False,
            ).select_related("remote_property", "local_instance")
        }
        price_data = self._resolve_price_data(
            product=product,
            prices=prices,
        )
        content_payload = self._resolve_content_payload(product=content_product)
        fallback_name = getattr(translation, "name", None) or getattr(content_product, "name", None) or getattr(product, "name", "") or ""

        return {
            "product": product,
            "parent_product": self.local_product if self.local_product and self.local_product.is_configurable() else None,
            "content_product": content_product,
            "translation": translation,
            "product_type": product_type,
            "category_remote_id": getattr(product_type, "remote_id", "") or "",
            "product_properties": product_properties,
            "property_by_id": property_by_id,
            "remote_select_lookup": remote_select_lookup,
            "images": images,
            "swatch_url": self._resolve_swatch_url(images=images, product_properties=product_properties),
            "ean": ean,
            "price_data": price_data,
            "sku": getattr(product, "sku", "") or "",
            "name": self._stringify(content_payload.get("name")) or fallback_name,
            "short_description": self._normalize_content_value(content_payload.get("shortDescription")),
            "description": self._normalize_content_value(content_payload.get("description")),
            "bullet_points": [self._stringify(point) for point in content_payload.get("bulletPoints", []) if self._stringify(point)],
            "url_key": getattr(translation, "url_key", None) or "",
        }

    def _build_row(self, *, product_context: dict[str, Any]) -> dict[str, str]:
        row: dict[str, str] = {}
        header_items = self._get_header_items(product_type=product_context["product_type"])
        missing_mapping_errors: list[str] = []
        preflight_errors: list[str] = []
        bullet_indexes = self._build_representation_indexes(
            header_items=header_items,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT,
        )
        image_indexes = self._build_representation_indexes(
            header_items=header_items,
            representation_type=MiraklProperty.REPRESENTATION_IMAGE,
        )
        product_context["_has_thumbnail_header"] = any(
            self._get_effective_representation_type(remote_property=item.remote_property) == MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE
            for item in header_items
        )
        product_context["_has_swatch_header"] = any(
            self._get_effective_representation_type(remote_property=item.remote_property) == MiraklProperty.REPRESENTATION_SWATCH_IMAGE
            for item in header_items
        )

        for product_type_item in header_items:
            try:
                value = self._resolve_property_value(
                    product_type_item=product_type_item,
                    product_context=product_context,
                    bullet_index=bullet_indexes.get(product_type_item.id),
                    image_index=image_indexes.get(product_type_item.id),
                )
            except MissingMappingError as exc:
                missing_mapping_errors.append(str(exc))
                continue
            except PreFlightCheckError as exc:
                preflight_errors.append(str(exc))
                continue
            row[product_type_item.remote_property.code] = value

        if missing_mapping_errors or preflight_errors:
            self._raise_collected_row_errors(
                missing_mapping_errors=missing_mapping_errors,
                preflight_errors=preflight_errors,
            )

        row.update(self._build_offer_fields(product_context=product_context))
        return row

    def _raise_collected_row_errors(
        self,
        *,
        missing_mapping_errors: list[str],
        preflight_errors: list[str],
    ) -> None:
        missing_mapping_errors = self._dedupe_errors(errors=missing_mapping_errors)
        preflight_errors = self._dedupe_errors(errors=preflight_errors)

        message_parts: list[str] = []
        if missing_mapping_errors:
            message_parts.append(
                "Missing Mirakl mappings:\n- " + "\n- ".join(missing_mapping_errors)
            )
        if preflight_errors:
            message_parts.append(
                "Mirakl preflight errors:\n- " + "\n- ".join(preflight_errors)
            )
        message = "\n\n".join(message_parts)

        if preflight_errors:
            raise PreFlightCheckError(message)
        raise MissingMappingError(message)

    def _dedupe_errors(self, *, errors: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for error in errors:
            normalized_error = str(error).strip()
            if not normalized_error or normalized_error in seen:
                continue
            seen.add(normalized_error)
            ordered.append(normalized_error)
        return ordered

    def _build_offer_fields(self, *, product_context: dict[str, Any]) -> dict[str, str]:
        price_data = product_context["price_data"]
        description = product_context["description"]
        short_description = product_context["short_description"]
        price = self._stringify(price_data.get("full_price"))
        quantity = self._resolve_create_quantity()
        if self.action == SalesChannelFeedItem.ACTION_DELETE:
            if not description:
                description = self._default_delete_text()
            if not short_description:
                short_description = self._default_delete_text()
            if not price:
                price = "0"
            if not quantity:
                quantity = "0"
        return {
            "sku": product_context["sku"],
            "product-id": product_context["sku"],
            "product-id-type": "SHOP_SKU",
            "description": description,
            "internal-description": short_description,
            "price": price,
            "price-additional-info": "",
            "quantity": quantity,
            "min-quantity-alert": "",
            "state": self._resolve_offer_state(product_context=product_context),
            "available-start-date": "",
            "available-end-date": "",
            "logistic-class": "",
            "discount-price": self._stringify(price_data.get("discounted_price")),
            "discount-start-date": self._format_date(price_data.get("start_date")),
            "discount-end-date": self._format_date(price_data.get("end_date")),
            "leadtime-to-ship": "",
            "update-delete": self.action.upper(),
        }

    def _resolve_create_quantity(self) -> str:
        if self.action != SalesChannelFeedItem.ACTION_CREATE:
            return ""
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock in (None, ""):
            return ""
        return self._stringify(max(int(starting_stock), 0))

    def _resolve_offer_state(self, *, product_context: dict[str, Any]) -> str:
        remote_property = self._get_condition_property()
        if remote_property is None:
            return ""
        return self._resolve_condition(
            remote_property=remote_property,
            product_context=product_context,
        )

    def _get_condition_property(self) -> MiraklProperty | None:
        if self._condition_property_cache is self._UNSET:
            self._condition_property_cache = (
                MiraklProperty.objects.filter(
                    sales_channel=self.sales_channel,
                    representation_type=MiraklProperty.REPRESENTATION_CONDITION,
                )
                .order_by("id")
                .first()
            )
        return None if self._condition_property_cache is self._UNSET else self._condition_property_cache

    def _resolve_product_type(self, *, product: Product) -> MiraklProductType | None:
        category_mapping = (
            MiraklProductCategory.objects.filter(
                product=product,
                sales_channel=self.sales_channel,
            )
            .exclude(remote_id__in=(None, ""))
            .order_by("id")
            .first()
        )
        category_remote_id = getattr(category_mapping, "remote_id", "") or ""
        if category_remote_id:
            cache_key = (product.id, 1)
            if cache_key not in self._product_type_cache:
                self._product_type_cache[cache_key] = (
                    MiraklProductType.objects.filter(
                        sales_channel=self.sales_channel,
                        remote_id=category_remote_id,
                    )
                    .select_related("category", "local_instance")
                    .first()
                )
            product_type = self._product_type_cache[cache_key]
            if product_type is not None:
                return product_type

        product_rule = product.get_product_rule(sales_channel=self.sales_channel)
        if product_rule is None:
            return None
        cache_key = (product.id, 2)
        if cache_key not in self._product_type_cache:
            self._product_type_cache[cache_key] = (
                MiraklProductType.objects.filter(
                    sales_channel=self.sales_channel,
                    local_instance=product_rule,
                )
                .select_related("category", "local_instance")
                .first()
            )
        return self._product_type_cache[cache_key]

    def _get_header_items(self, *, product_type: MiraklProductType) -> list[MiraklProductTypeItem]:
        items = (
            MiraklProductTypeItem.objects.filter(product_type=product_type)
            .select_related(
                "remote_property",
                "remote_property__local_instance",
                "local_instance",
                "local_instance__property",
            )
            .prefetch_related("remote_property__applicabilities")
            .order_by("id")
        )
        view_id = getattr(self.sales_channel_view, "id", self.sales_channel_view)
        filtered: list[MiraklProductTypeItem] = []
        for item in items:
            if str(item.requirement_level or "").upper() == "DISABLED":
                continue
            applicability_view_ids = [applicability.view_id for applicability in item.remote_property.applicabilities.all()]
            if view_id not in applicability_view_ids:
                continue
            filtered.append(item)
        return filtered

    def _load_translations(self, *, products: list[Product]) -> dict[int, list[ProductTranslation]]:
        queryset = ProductTranslation.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        results: dict[int, list[ProductTranslation]] = defaultdict(list)
        for translation in queryset.iterator():
            results[translation.product_id].append(translation)
        return results

    def _load_properties(self, *, products: list[Product]) -> dict[int, list[ProductProperty]]:
        queryset = (
            ProductProperty.objects.filter(product_id__in=[product.id for product in products])
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select", "value_multi_select__image")
            .order_by("product_id", "id")
        )
        results: dict[int, list[ProductProperty]] = defaultdict(list)
        for item in queryset:
            results[item.product_id].append(item)
        return results

    def _load_prices(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
        product_ids = [product.id for product in products]
        channel_pricelists = list(
            SalesChannelIntegrationPricelist.objects.filter(sales_channel=self.sales_channel).select_related("price_list__currency")
        )
        if not channel_pricelists:
            return {}

        queryset = (
            SalesPriceListItem.objects.filter(
                product_id__in=product_ids,
                salespricelist__in=[item.price_list for item in channel_pricelists],
            )
            .select_related("salespricelist", "salespricelist__currency")
            .order_by("product_id", "id")
        )
        results: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in queryset.iterator():
            price = getattr(item, "price", None)
            discount = getattr(item, "discount", None)
            if price is None and discount is None:
                continue
            results[item.product_id].append(
                {
                    "currency": getattr(getattr(item.salespricelist, "currency", None), "iso_code", "") or "",
                    "full_price": price,
                    "discounted_price": discount,
                    "start_date": getattr(item.salespricelist, "start_date", None),
                    "end_date": getattr(item.salespricelist, "end_date", None),
                }
            )
        return results

    def _load_media(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
        queryset = (
            MediaProductThrough.objects.filter(product_id__in=[product.id for product in products])
            .select_related("media", "sales_channel")
            .order_by("product_id", "-is_main_image", "sort_order", "id")
        )
        results: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in queryset.iterator():
            if item.sales_channel_id not in (None, self.sales_channel.id):
                continue
            media = item.media
            if media.type != Media.IMAGE:
                continue
            url = media.image_url()
            if not url:
                continue
            results[item.product_id].append(
                {
                    "url": url,
                    "is_main": bool(item.is_main_image),
                    "is_swatch": media.image_type == Media.COLOR_SHOT,
                    "sort_order": item.sort_order,
                }
            )
        return results

    def _load_eans(self, *, products: list[Product]) -> dict[int, str]:
        queryset = EanCode.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        return {ean.product_id: ean.ean_code for ean in queryset.iterator() if ean.ean_code}

    def _select_translation(self, *, translations: list[ProductTranslation]) -> ProductTranslation | None:
        if not translations:
            return None
        if self.language:
            for translation in translations:
                if translation.language == self.language and translation.sales_channel_id in (None, self.sales_channel.id):
                    return translation
            for translation in translations:
                if translation.language == self.language:
                    return translation
        for translation in translations:
            if translation.sales_channel_id in (None, self.sales_channel.id):
                return translation
        return translations[0]

    def _resolve_price_data(self, *, product: Product, prices: list[dict[str, Any]]) -> dict[str, Any]:
        primary_price = self._get_primary_price(prices=prices)
        if primary_price:
            return primary_price
        full_price, discounted_price = product.get_price_for_sales_channel(self.sales_channel)
        return {
            "full_price": full_price,
            "discounted_price": discounted_price,
            "start_date": None,
            "end_date": None,
        }

    def _get_primary_price(self, *, prices: list[dict[str, Any]]) -> dict[str, Any]:
        if not prices:
            return {}
        today = date.today()
        for price in prices:
            start_date = price.get("start_date")
            end_date = price.get("end_date")
            if start_date and end_date and start_date <= today <= end_date:
                return price
        for price in prices:
            if not price.get("start_date") and not price.get("end_date"):
                return price
        return prices[0]

    def _resolve_property_value(
        self,
        *,
        product_type_item: MiraklProductTypeItem,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        remote_property = product_type_item.remote_property
        representation_type = self._get_effective_representation_type(remote_property=remote_property)
        resolver_name = f"_resolve_{representation_type}"
        resolver = getattr(self, resolver_name, None)
        if resolver is None:
            resolver = self._resolve_property
        value = resolver(
            remote_property=remote_property,
            product_context=product_context,
            bullet_index=bullet_index,
            image_index=image_index,
        )
        if (
            value in (None, "")
            and self.action == SalesChannelFeedItem.ACTION_DELETE
            and self._is_required_product_type_item(product_type_item=product_type_item, product_context=product_context)
        ):
            value = self._build_delete_placeholder(
                remote_property=remote_property,
                product_context=product_context,
            )
        value = self._apply_remote_validations(remote_property=remote_property, value=value, product_context=product_context)
        if value in (None, "") and self._is_required_product_type_item(product_type_item=product_type_item, product_context=product_context):
            if self._is_missing_required_mapping(
                product_type_item=product_type_item,
                representation_type=representation_type,
            ):
                raise MissingMappingError(
                    f"Map Mirakl field '{remote_property.code}'"
                )
            raise PreFlightCheckError(
                self._build_missing_required_value_message(
                    remote_property=remote_property,
                    product_context=product_context,
                )
            )
        return self._stringify(value)

    def _build_missing_required_value_message(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
    ) -> str:
        product = product_context.get("product")
        product_label = product_context["sku"]
        local_instance = getattr(remote_property, "local_instance", None)
        if local_instance is None:
            return (
                f"Mirakl required field '{remote_property.code}' is missing for product {product_label}."
            )

        local_property_label = (
            getattr(local_instance, "internal_name", None)
            or getattr(local_instance, "name", None)
            or str(local_instance.id)
        )
        parent_product = product_context.get("parent_product")
        if product is not None and parent_product is not None and getattr(product, "id", None) != getattr(parent_product, "id", None):
            return (
                f"Mirakl required property '{remote_property.code}' (local '{local_property_label}') "
                f"has no value for variation product {product_label}."
            )
        return (
            f"Mirakl required property '{remote_property.code}' (local '{local_property_label}') "
            f"has no value for product {product_label}."
        )

    def _is_missing_required_mapping(
        self,
        *,
        product_type_item: MiraklProductTypeItem,
        representation_type: str,
    ) -> bool:
        remote_property = product_type_item.remote_property
        if representation_type not in {
            MiraklProperty.REPRESENTATION_PROPERTY,
            MiraklProperty.REPRESENTATION_UNIT,
            MiraklProperty.REPRESENTATION_CONDITION,
        }:
            return False
        if getattr(remote_property, "local_instance_id", None):
            return False
        if self._get_effective_default_value(remote_property=remote_property):
            return False
        return True

    def _get_effective_representation_type(self, *, remote_property: MiraklProperty) -> str:
        representation_type = str(getattr(remote_property, "representation_type", "") or "")
        if representation_type and representation_type != MiraklProperty.REPRESENTATION_PROPERTY:
            return representation_type

        normalized_code = re.sub(r"[^a-z0-9]+", "_", str(getattr(remote_property, "code", "") or "").strip().lower()).strip("_")
        if normalized_code in {"product_id", "sku", "product_sku", "shop_sku"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_SKU
        if normalized_code in {"parent_product_id", "parent_sku", "configurable_sku"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU
        if normalized_code in {"variant_group_code", "configurable_id"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_ID
        if normalized_code == "ean" or normalized_code.endswith("_ean") or "ean_code" in normalized_code:
            return MiraklProperty.REPRESENTATION_PRODUCT_EAN
        if normalized_code.startswith("long_description") or normalized_code.startswith("details_and_care"):
            return MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION
        return representation_type or MiraklProperty.REPRESENTATION_PROPERTY

    def _resolve_property(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        product_property = product_context["property_by_id"].get(remote_property.local_instance_id)
        if product_property is None:
            default_value = self._get_effective_default_value(remote_property=remote_property)
            if default_value:
                return default_value
            if remote_property.local_instance_id is None:
                return ""
            return ""
        return self._serialize_property_value(
            product_property=product_property,
            remote_property=remote_property,
            remote_value_lookup=product_context["remote_select_lookup"],
        )

    def _resolve_unit(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        return self._resolve_property(remote_property=remote_property, product_context=product_context)

    def _resolve_default_value(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        return self._get_effective_default_value(remote_property=remote_property)

    def _resolve_product_title(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["name"]

    def _resolve_product_subtitle(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        translation = product_context["translation"]
        return getattr(translation, "subtitle", None) or ""

    def _resolve_product_description(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["description"]

    def _resolve_product_short_description(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["short_description"]

    def _resolve_product_bullet_point(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        bullet_points = list(product_context.get("bullet_points") or [])
        if not bullet_points:
            bullet_points = self._split_bullet_points(
                product_context["short_description"],
                product_context["description"],
            )
        if bullet_index is not None:
            index = bullet_index
        else:
            index = self._extract_numeric_suffix(remote_property.code) - 1
        if index < 0:
            index = 0
        return bullet_points[index] if index < len(bullet_points) else ""

    def _resolve_product_sku(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["sku"]

    def _resolve_product_internal_id(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return str(product_context["product"].id)

    def _resolve_product_category(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["category_remote_id"]

    def _resolve_product_configurable_sku(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        parent_product = product_context["parent_product"]
        return getattr(parent_product, "sku", "") or ""

    def _resolve_product_configurable_id(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        parent_product = product_context["parent_product"]
        if parent_product is None:
            return ""
        return str(parent_product.id)

    def _resolve_product_active(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_boolean_value(
            remote_property=remote_property,
            value=bool(getattr(product_context["product"], "active", False)),
        )

    def _resolve_product_url_key(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["url_key"]

    def _resolve_product_ean(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["ean"]

    def _resolve_thumbnail_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._get_main_image_url(images=product_context["images"])

    def _resolve_swatch_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["swatch_url"]

    def _resolve_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        if image_index is None:
            additional_match = re.search(r"additional_(\d+)", remote_property.code or "")
            image_index = int(additional_match.group(1)) - 1 if additional_match else 0
        return self._get_ranked_image_url(
            images=product_context["images"],
            index=image_index,
            has_thumbnail_header=bool(product_context.get("_has_thumbnail_header")),
            has_swatch_header=bool(product_context.get("_has_swatch_header")),
            swatch_url=product_context.get("swatch_url", ""),
        )

    def _resolve_video(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return ""

    def _resolve_document(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return ""

    def _resolve_price(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._stringify(product_context["price_data"].get("full_price"))

    def _resolve_discounted_price(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._stringify(product_context["price_data"].get("discounted_price"))

    def _resolve_stock(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_create_quantity()

    def _resolve_vat_rate(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        vat_rate = getattr(product_context["product"], "vat_rate", None)
        rate = getattr(vat_rate, "rate", None)
        return "" if rate in (None, "") else self._stringify(rate)

    def _resolve_allow_backorder(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_boolean_value(
            remote_property=remote_property,
            value=bool(getattr(product_context["product"], "allow_backorder", False)),
        )

    def _resolve_condition(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_property(
            remote_property=remote_property,
            product_context=product_context,
        )

    def _serialize_property_value(
        self,
        *,
        product_property: ProductProperty,
        remote_property: MiraklProperty,
        remote_value_lookup: dict[tuple[int, int], MiraklPropertySelectValue],
    ) -> str:
        property_type = getattr(product_property.property, "type", "")
        if property_type == "SELECT" and product_property.value_select_id:
            mapped_value = remote_value_lookup.get((remote_property.id, product_property.value_select_id))
            if mapped_value is None:
                raise MissingMappingError(
                    f"Map the OneSila select value for Mirakl field '{remote_property.code}' before pushing."
                )
            return self._stringify(getattr(mapped_value, "value", None) or getattr(mapped_value, "code", None))
        if property_type == "MULTISELECT":
            values: list[str] = []
            for select_value in product_property.value_multi_select.all():
                mapped_value = remote_value_lookup.get((remote_property.id, select_value.id))
                if mapped_value is None:
                    raise MissingMappingError(
                        f"Map all OneSila multiselect values for Mirakl field '{remote_property.code}' before pushing."
                    )
                values.append(self._stringify(getattr(mapped_value, "value", None) or getattr(mapped_value, "code", None)))
            separator = getattr(self.sales_channel, "list_of_multiple_values_separator", None) or ","
            return separator.join([value for value in values if value])
        return self._stringify(product_property.get_serialised_value(self.language))

    def _resolve_boolean_value(self, *, remote_property: MiraklProperty, value: bool) -> str:
        yes_text_value, no_text_value = self._get_effective_boolean_text_values(remote_property=remote_property)
        if remote_property.type == "BOOLEAN":
            if value and yes_text_value:
                return self._stringify(yes_text_value)
            if not value and no_text_value:
                return self._stringify(no_text_value)
            return "true" if value else "false"

        if remote_property.type == "SELECT":
            mapped_value = MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
                bool_value=value,
            ).order_by("id").first()
            if mapped_value is not None:
                return self._stringify(mapped_value.value or mapped_value.code)

        return "true" if value else "false"

    def _apply_remote_validations(self, *, remote_property: MiraklProperty, value: Any, product_context: dict[str, Any]) -> Any:
        if str(getattr(remote_property, "type", "") or "").upper() in {"SELECT", "MULTISELECT"}:
            return value

        value = self._apply_type_parameter_transforms(
            remote_property=remote_property,
            value=value,
        )
        rendered = self._stringify(value)
        if rendered == "":
            return value

        for entry in self._get_validation_entries(remote_property=remote_property):
            parts = [part.strip() for part in str(entry).split("|") if part.strip()]
            if len(parts) < 2:
                continue
            rule = parts[0].upper()

            if rule == "MAX_LENGTH":
                try:
                    limit = int(parts[1])
                except (TypeError, ValueError):
                    continue
                if len(rendered) > limit:
                    rendered = rendered[:limit]
                continue

            if rule == "MIN_LENGTH":
                try:
                    limit = int(parts[1])
                except (TypeError, ValueError):
                    continue
                if len(rendered) < limit:
                    raise MiraklPayloadValidationError(
                        f"Mirakl field '{remote_property.code}' is shorter than min length {limit} for product {product_context['sku']}."
                    )
                continue

            if rule == "FORBIDDEN_WORDS":
                forbidden_words = [part.strip().lower() for part in parts[1].strip('"').split(",") if part.strip()]
                for forbidden_word in forbidden_words:
                    if not forbidden_word:
                        continue
                    matched_forbidden_word = self._find_matching_forbidden_word(
                        value=rendered,
                        forbidden_word=forbidden_word,
                    )
                    if matched_forbidden_word:
                        raise MiraklPayloadValidationError(
                            f"Mirakl field '{remote_property.code}' contains forbidden word '{matched_forbidden_word}' for product {product_context['sku']}."
                        )
                continue

            if rule == "PRODUCT_REFERENCE":
                allowed_reference_types = parts[1:]
                if not self._is_valid_product_reference(value=rendered, allowed_reference_types=allowed_reference_types):
                    raise MiraklPayloadValidationError(
                        f"Mirakl field '{remote_property.code}' is not a valid product reference for product {product_context['sku']}."
                    )

        return rendered

    def _apply_type_parameter_transforms(self, *, remote_property: MiraklProperty, value: Any) -> Any:
        transformed_value = self._apply_precision_type_parameter(
            remote_property=remote_property,
            value=value,
        )
        return self._apply_pattern_type_parameter(
            remote_property=remote_property,
            value=transformed_value,
        )

    def _apply_precision_type_parameter(self, *, remote_property: MiraklProperty, value: Any) -> Any:
        raw_precision = self._get_type_parameter_value(
            remote_property=remote_property,
            name="PRECISION",
        )
        if raw_precision == "" or value in (None, ""):
            return value
        try:
            precision = int(raw_precision)
        except (TypeError, ValueError):
            return value
        if precision < 0:
            return value

        numeric_value = self._truncate_decimal_value(value=value, precision=precision)
        if numeric_value is None:
            return value
        return numeric_value

    def _truncate_decimal_value(self, *, value: Any, precision: int) -> str | None:
        normalized_value = self._stringify(value).strip()
        if normalized_value == "":
            return ""
        try:
            decimal_value = Decimal(normalized_value)
        except (InvalidOperation, ValueError):
            return None

        exponent = Decimal("1").scaleb(-precision)
        quantized_value = decimal_value.quantize(exponent, rounding=ROUND_DOWN)
        rendered = format(quantized_value, "f")
        if precision == 0:
            return rendered.split(".", 1)[0]
        rendered = rendered.rstrip("0").rstrip(".")
        return rendered or "0"

    def _apply_pattern_type_parameter(self, *, remote_property: MiraklProperty, value: Any) -> Any:
        pattern = self._get_type_parameter_value(
            remote_property=remote_property,
            name="PATTERN",
        )
        if not pattern or value in (None, ""):
            return value
        return self._format_date(value=value, pattern=pattern)

    def _get_validation_entries(self, *, remote_property: MiraklProperty) -> list[str]:
        validations = remote_property.validations
        if isinstance(validations, str):
            return [validations]
        if isinstance(validations, list):
            return [str(entry) for entry in validations if entry not in (None, "")]
        if isinstance(validations, dict):
            entries: list[str] = []
            for key, value in validations.items():
                if key not in (None, ""):
                    entries.append(str(key))
                if isinstance(value, str) and value:
                    entries.append(value)
                if isinstance(value, list):
                    entries.extend(str(item) for item in value if item not in (None, ""))
            return entries
        return []

    def _build_delete_placeholder(self, *, remote_property: MiraklProperty, product_context: dict[str, Any]) -> str:
        select_placeholder = self._get_first_select_value(remote_property=remote_property)
        if select_placeholder:
            return select_placeholder

        reference_placeholder = self._build_delete_product_reference_placeholder(remote_property=remote_property)
        if reference_placeholder:
            return reference_placeholder

        remote_type = str(getattr(remote_property, "type", "") or "").upper()
        if remote_type in {"BOOLEAN"}:
            return self._resolve_boolean_value(remote_property=remote_property, value=False)
        if remote_type in {"NUMERIC"}:
            return "0"
        if remote_type == "DATE":
            return date.today().isoformat()
        return self._default_delete_text()

    def _get_first_select_value(self, *, remote_property: MiraklProperty) -> str:
        if str(getattr(remote_property, "type", "") or "").upper() not in {"SELECT", "MULTISELECT"}:
            return ""
        select_value = (
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
            )
            .order_by("id")
            .first()
        )
        if select_value is None:
            return ""
        return self._stringify(select_value.value or select_value.code or select_value.remote_id)

    def _build_delete_product_reference_placeholder(self, *, remote_property: MiraklProperty) -> str:
        for entry in self._get_validation_entries(remote_property=remote_property):
            parts = [part.strip() for part in str(entry).split("|") if part.strip()]
            if not parts or parts[0].upper() != "PRODUCT_REFERENCE":
                continue
            for reference_type in parts[1:]:
                normalized_type = str(reference_type or "").upper()
                if normalized_type == "EAN-8":
                    return "00000000"
                if normalized_type == "UPC":
                    return "000000000000"
                if normalized_type == "EAN-13":
                    return "0000000000000"
        return ""

    def _is_valid_product_reference(self, *, value: str, allowed_reference_types: list[str]) -> bool:
        normalized_value = re.sub(r"\s+", "", str(value or ""))
        if not normalized_value.isdigit():
            return False
        length_map = {
            "EAN-8": 8,
            "UPC": 12,
            "EAN-13": 13,
        }
        for reference_type in allowed_reference_types:
            expected_length = length_map.get(str(reference_type or "").upper())
            if expected_length is not None and len(normalized_value) == expected_length:
                return True
        return False

    def _find_matching_forbidden_word(self, *, value: str, forbidden_word: str) -> str:
        value_tokens = self._tokenize_forbidden_words_value(value=value)
        forbidden_tokens = self._tokenize_forbidden_words_value(value=forbidden_word)
        if not value_tokens or not forbidden_tokens:
            return ""
        max_start = len(value_tokens) - len(forbidden_tokens)
        for start_index in range(max_start + 1):
            if value_tokens[start_index:start_index + len(forbidden_tokens)] == forbidden_tokens:
                return " ".join(forbidden_tokens)
        return ""

    def _tokenize_forbidden_words_value(self, *, value: str) -> list[str]:
        return [token for token in re.findall(r"[a-z0-9]+", str(value or "").lower()) if token]

    def _default_delete_text(self) -> str:
        return "TO_BE_DELETED"

    def _build_representation_indexes(self, *, header_items: list[MiraklProductTypeItem], representation_type: str) -> dict[int, int]:
        matches = [
            item
            for item in header_items
            if self._get_effective_representation_type(remote_property=item.remote_property) == representation_type
        ]
        return {item.id: index for index, item in enumerate(matches)}

    def _resolve_swatch_url(self, *, images: list[dict[str, Any]], product_properties: list[ProductProperty]) -> str:
        for image in images:
            if image.get("is_swatch"):
                return self._stringify(image.get("url"))

        for product_property in product_properties:
            prop = product_property.property
            if not getattr(prop, "has_image", False):
                continue
            select_value = getattr(product_property, "value_select", None)
            image = getattr(select_value, "image", None)
            if image and hasattr(image, "image_url"):
                return self._stringify(image.image_url())
        return ""

    def _get_main_image_url(self, *, images: list[dict[str, Any]]) -> str:
        for image in images:
            if image.get("is_main"):
                return self._stringify(image.get("url"))
        if images:
            return self._stringify(images[0].get("url"))
        return ""

    def _get_ranked_image_url(
        self,
        *,
        images: list[dict[str, Any]],
        index: int,
        has_thumbnail_header: bool,
        has_swatch_header: bool,
        swatch_url: str,
    ) -> str:
        main_image_url = self._get_main_image_url(images=images)
        candidate_urls: list[str] = []
        seen: set[str] = set()
        for image in images:
            url = self._stringify(image.get("url"))
            if not url or url in seen:
                continue
            if has_thumbnail_header and url == main_image_url:
                continue
            if has_swatch_header and swatch_url and url == swatch_url:
                continue
            seen.add(url)
            candidate_urls.append(url)
        if not candidate_urls and not has_thumbnail_header and main_image_url:
            return main_image_url
        return candidate_urls[index] if 0 <= index < len(candidate_urls) else ""

    def _split_bullet_points(self, *values: str) -> list[str]:
        bullets: list[str] = []
        for value in values:
            for part in re.split(r"[\n\r]+|•", str(value or "")):
                part = part.strip()
                if part:
                    bullets.append(part)
        return bullets

    def _extract_numeric_suffix(self, value: str) -> int:
        match = re.search(r"(\d+)(?!.*\d)", str(value or ""))
        return int(match.group(1)) if match else 1

    def _is_required_product_type_item(self, *, product_type_item: MiraklProductTypeItem, product_context: dict[str, Any]) -> bool:
        representation_type = self._get_effective_representation_type(remote_property=product_type_item.remote_property)
        if representation_type in {
            MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
            MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_ID,
        } and product_context.get("parent_product") is None:
            return False
        return bool(product_type_item.required or str(product_type_item.requirement_level or "").upper() == "REQUIRED")

    def _get_effective_default_value(self, *, remote_property: MiraklProperty) -> str:
        public_definition = self._get_public_definition(remote_property=remote_property)
        if public_definition is not None and public_definition.default_value:
            return self._resolve_select_backed_default_value(
                remote_property=remote_property,
                raw_default=public_definition.default_value,
            )
        return self._resolve_select_backed_default_value(
            remote_property=remote_property,
            raw_default=remote_property.default_value or "",
        )

    def _get_effective_boolean_text_values(self, *, remote_property: MiraklProperty) -> tuple[str, str]:
        public_definition = self._get_public_definition(remote_property=remote_property)
        if public_definition is not None:
            return (
                public_definition.yes_text_value or remote_property.yes_text_value or "",
                public_definition.no_text_value or remote_property.no_text_value or "",
            )
        return remote_property.yes_text_value or "", remote_property.no_text_value or ""

    def _get_public_definition(self, *, remote_property: MiraklProperty) -> MiraklPublicDefinition | None:
        if not getattr(remote_property, "representation_type_decided", False):
            return None
        if remote_property.code not in self._public_definition_cache:
            self._public_definition_cache[remote_property.code] = (
                MiraklPublicDefinition.objects.filter(
                    hostname=self.sales_channel.hostname,
                    property_code=remote_property.code,
                )
                .order_by("id")
                .first()
            )
        return self._public_definition_cache[remote_property.code]

    def _resolve_select_backed_default_value(self, *, remote_property: MiraklProperty, raw_default: str) -> str:
        normalized_default = self._stringify(raw_default)
        if normalized_default == "":
            return ""
        if remote_property.type not in {"SELECT", "MULTISELECT"}:
            return normalized_default

        select_values = list(
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
            ).order_by("id")[:2]
        )
        if len(select_values) == 1:
            return self._stringify(select_values[0].value or select_values[0].code or normalized_default)

        match = (
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
            )
            .filter(code=normalized_default)
            .order_by("id")
            .first()
        )
        if match is None:
            match = (
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                    remote_id=normalized_default,
                )
                .order_by("id")
                .first()
            )
        if match is None:
            match = (
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                    value=normalized_default,
                )
                .order_by("id")
                .first()
            )
        if match is not None:
            return self._stringify(match.value or match.code or normalized_default)
        return normalized_default

    def _format_date(self, value: Any, pattern: str = "") -> str:
        if value in (None, ""):
            return ""
        parsed_value = self._coerce_temporal_value(value=value)
        if parsed_value is None:
            return self._stringify(value)
        if pattern:
            strftime_pattern = self._mirakl_pattern_to_strftime(pattern=pattern)
            if strftime_pattern:
                return parsed_value.strftime(strftime_pattern)
        if isinstance(parsed_value, datetime):
            return parsed_value.date().isoformat()
        return parsed_value.isoformat()

    def _coerce_temporal_value(self, *, value: Any) -> date | datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return value
        normalized_value = self._stringify(value).strip()
        if not normalized_value:
            return None
        normalized_value = normalized_value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized_value)
        except ValueError:
            pass
        try:
            return date.fromisoformat(normalized_value)
        except ValueError:
            return None

    def _mirakl_pattern_to_strftime(self, *, pattern: str) -> str:
        rendered_pattern = str(pattern or "")
        replacements = [
            ("yyyy", "%Y"),
            ("MM", "%m"),
            ("dd", "%d"),
            ("HH", "%H"),
            ("mm", "%M"),
            ("ss", "%S"),
        ]
        for source, target in replacements:
            rendered_pattern = rendered_pattern.replace(source, target)
        return rendered_pattern if "%" in rendered_pattern else ""

    def _get_type_parameter_value(self, *, remote_property: MiraklProperty, name: str) -> str:
        return get_mirakl_type_parameter_value(
            raw_value=getattr(remote_property, "type_parameters", None),
            name=name,
        )

    def _resolve_content_payload(self, *, product: Product) -> dict[str, Any]:
        content_data = build_content_data(
            product=product,
            sales_channel=self.sales_channel,
        )
        if not content_data:
            return {}

        preferred_languages: list[str] = []
        if self.language:
            preferred_languages.append(str(self.language))
        preferred_languages.extend([language for language in content_data.keys() if language not in preferred_languages])

        for language in preferred_languages:
            payload = content_data.get(language)
            if payload:
                return payload
        return {}

    def _normalize_content_value(self, value: Any) -> str:
        if _content_is_empty(value):
            return ""
        return self._stringify(value)

    def _stringify(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        return str(value)


class _MiraklFeedPersistenceMixin:
    feed_action = SalesChannelFeedItem.ACTION_UPDATE

    def _persist_feed_rows(self, *, product_type: MiraklProductType, rows: list[dict[str, str]]):
        if not rows:
            return None

        feed = self._get_or_create_feed(product_type=product_type)
        identifier = self._get_identifier()
        with transaction.atomic():
            item = (
                MiraklSalesChannelFeedItem.objects.select_for_update()
                .filter(
                    feed=feed,
                    remote_product=self.remote_instance,
                    sales_channel_view=self.view,
                )
                .first()
            )
            merged_action = self._merge_action(
                current_action=getattr(item, "action", ""),
                new_action=self.feed_action,
            )
            if item is None:
                item = MiraklSalesChannelFeedItem.objects.create(
                    feed=feed,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    remote_product=self.remote_instance,
                    sales_channel_view=self.view,
                    action=merged_action,
                    identifier=identifier,
                    payload_data=rows,
                    status=SalesChannelFeedItem.STATUS_PENDING,
                    result_data={},
                    error_message="",
                )
            else:
                item.action = merged_action
                item.identifier = identifier
                item.payload_data = rows
                item.status = SalesChannelFeedItem.STATUS_PENDING
                item.result_data = {}
                item.error_message = ""
                item.save(
                    update_fields=[
                        "action",
                        "identifier",
                        "payload_data",
                        "status",
                        "result_data",
                        "error_message",
                    ]
                )
        self._refresh_feed_summary(feed=feed)
        return item

    def _get_or_create_feed(self, *, product_type: MiraklProductType) -> MiraklSalesChannelFeed:
        with transaction.atomic():
            feed = (
                MiraklSalesChannelFeed.objects.select_for_update()
                .filter(
                    sales_channel=self.sales_channel,
                    type=MiraklSalesChannelFeed.TYPE_PRODUCT,
                    stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
                    status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
                    product_type=product_type,
                    sales_channel_view=self.view,
                )
                .order_by("-updated_at")
                .first()
            )
            if feed is not None:
                return feed

            return MiraklSalesChannelFeed.objects.create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                type=MiraklSalesChannelFeed.TYPE_PRODUCT,
                stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
                status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
                product_type=product_type,
                sales_channel_view=self.view,
                raw_data={},
            )

    def _refresh_feed_summary(self, *, feed: MiraklSalesChannelFeed) -> None:
        items = list(
            MiraklSalesChannelFeedItem.objects.filter(feed=feed).only("payload_data")
        )
        feed.items_count = len(items)
        feed.rows_count = sum(len(item.payload_data or []) for item in items)
        feed.save(update_fields=["items_count", "rows_count", "updated_at"])

    def _get_identifier(self) -> str:
        local_product = getattr(self.remote_instance, "local_instance", None)
        return getattr(local_product, "sku", "") or getattr(self.remote_instance, "remote_sku", "") or ""

    def _merge_action(self, *, current_action: str, new_action: str) -> str:
        if new_action == SalesChannelFeedItem.ACTION_DELETE:
            return SalesChannelFeedItem.ACTION_DELETE
        if current_action == SalesChannelFeedItem.ACTION_CREATE and new_action == SalesChannelFeedItem.ACTION_UPDATE:
            return SalesChannelFeedItem.ACTION_CREATE
        return new_action or current_action or SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductBaseFactory(GetMiraklAPIMixin, _MiraklFeedPersistenceMixin):
    remote_model_class = MiraklProduct
    remote_price_class = MiraklPrice
    remote_product_content_class = MiraklProductContent
    remote_product_eancode_class = MiraklEanCode

    REMOTE_TYPE_SIMPLE = "PRODUCT"
    REMOTE_TYPE_CONFIGURABLE = "PRODUCT"

    field_mapping = {}
    integration_has_documents = False

    def get_sync_product_factory(self):
        return MiraklProductSyncFactory

    def get_create_product_factory(self):
        return MiraklProductCreateFactory

    def get_delete_product_factory(self):
        return MiraklProductDeleteFactory

    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    def __init__(self, *args, view=None, force_validation_only: bool = False, force_full_update: bool = False, **kwargs):
        if view is None:
            raise ValueError("Mirakl product factories require a view argument.")

        self.view = view
        self.force_validation_only = force_validation_only
        self.force_full_update = force_full_update
        super().__init__(*args, **kwargs)

    def get_identifiers(self, *, fixing_caller: str = "run"):
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = MiraklProductBaseFactory.__name__

        fixing_class = getattr(self, "fixing_identifier_class", None)
        fixing_identifier = None
        if fixing_caller and fixing_class:
            fixing_identifier = f"{fixing_class.__name__}:{fixing_caller}"

        return f"{class_name}:{caller}", fixing_identifier

    def run_create_flow(self):
        if self.create_product_factory is None:
            raise ValueError("create_product_factory must be specified in the RemoteProductSyncFactory.")

        fac = self.create_product_factory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            api=self.api,
            view=self.view,
            parent_local_instance=self.parent_local_instance,
            remote_parent_product=self.remote_parent_product,
            is_switched=True,
        )
        fac.run()
        self.remote_instance = fac.remote_instance

    def run_sync_flow(self):
        if self.sync_product_factory is None:
            raise ValueError("sync_product_factory must be specified in the RemoteProductCreateFactory.")

        sync_factory = self.sync_product_factory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=self.remote_instance,
            parent_local_instance=self.parent_local_instance,
            remote_parent_product=self.remote_parent_product,
            api=self.api,
            view=self.view,
            is_switched=True,
        )
        sync_factory.run()

    def should_skip_remote_product_property_mirror(self):
        return True

    def build_payload(self):
        self.set_sku()
        self.set_name()
        self.set_content()
        self.set_price()
        self.set_ean_code()
        self.set_active()
        self.set_allow_backorder()
        self.payload = {}

    def perform_remote_action(self):
        product_type, rows = MiraklProductPayloadBuilder(
            remote_product=self.remote_instance,
            sales_channel_view=self.view,
            action=self.feed_action,
        ).build()
        self.payload = {
            "rows": rows,
            "product_type_id": product_type.id,
            "sales_channel_view_id": self.view.id,
        }
        self._persist_feed_rows(product_type=product_type, rows=rows)

        self.remote_product = self.remote_instance
        return self.payload

    def set_discount(self):
        return

    def set_content_translations(self):
        return

    def assign_images(self):
        return

    def assign_documents(self):
        return

    def assign_ean_code(self):
        return

    def assign_saleschannels(self):
        return

    def update_multi_currency_prices(self):
        return

    def set_remote_configurator(self):
        return

    def create_or_update_children(self):
        return

    def add_variation_to_parent(self):
        return


class MiraklProductSyncFactory(MiraklProductBaseFactory, RemoteProductSyncFactory):
    fixing_identifier_class = MiraklProductBaseFactory
    feed_action = SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductCreateFactory(MiraklProductBaseFactory, RemoteProductCreateFactory):
    fixing_identifier_class = MiraklProductBaseFactory
    feed_action = SalesChannelFeedItem.ACTION_CREATE

    def get_saleschannel_remote_object(self, remote_sku):
        return None


class MiraklProductUpdateFactory(MiraklProductSyncFactory):
    fixing_identifier_class = MiraklProductBaseFactory
    feed_action = SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductDeleteFactory(GetMiraklAPIMixin, _MiraklFeedPersistenceMixin, RemoteProductDeleteFactory):
    fixing_identifier_class = MiraklProductBaseFactory
    remote_model_class = MiraklProduct
    delete_remote_instance = False
    feed_action = SalesChannelFeedItem.ACTION_DELETE

    def __init__(self, *args, view=None, **kwargs):
        if view is None:
            raise ValueError("Mirakl product factories require a view argument.")
        self.view = view
        super().__init__(*args, **kwargs)
        if self.local_instance is None and getattr(self, "remote_instance", None) is not None:
            self.local_instance = self.remote_instance.local_instance

    def preflight_process(self):
        return

    def delete_remote(self):
        if self.remote_instance is None:
            return {}
        product_type, rows = MiraklProductPayloadBuilder(
            remote_product=self.remote_instance,
            sales_channel_view=self.view,
            action=self.feed_action,
        ).build()
        self.payload = {
            "rows": rows,
            "product_type_id": product_type.id,
            "sales_channel_view_id": self.view.id,
        }
        self._persist_feed_rows(product_type=product_type, rows=rows)
        return {}

    def serialize_response(self, response):
        return response


class _BaseMiraklProductPayloadFactory:
    action = SalesChannelFeedItem.ACTION_UPDATE

    def __init__(self, *, remote_product, sales_channel_view=None) -> None:
        self.remote_product = remote_product
        self.sales_channel_view = sales_channel_view

    def build(self) -> list[dict[str, str]]:
        _product_type, rows = MiraklProductPayloadBuilder(
            remote_product=self.remote_product,
            sales_channel_view=self.sales_channel_view,
            action=self.action,
        ).build()
        return rows


class MiraklProductCreatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_CREATE


class MiraklProductUpdatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductDeletePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_DELETE
