from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
import json
from typing import Any, Dict, Iterable, List, Tuple

from django.db.models import Q

from media.models import Media, MediaProductThrough
from products.models import ProductTranslation
from properties.models import ProductProperty, Property
from sales_channels.models.sales_channels import SalesChannelViewAssign

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models.products import EbayMediaThroughProduct
from sales_channels.integrations.ebay.models.properties import (
    EbayInternalProperty,
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
)


class EbayInventoryItemPayloadMixin(GetEbayAPIMixin):
    """Utilities for building full eBay inventory item payloads."""

    remote_model_class = EbayMediaThroughProduct
    remote_eancode_update_factory = None

    def __init__(self, *args: Any, get_value_only: bool = False, **kwargs: Any) -> None:
        if not hasattr(self, "view") or self.view is None:
            raise ValueError("Ebay factories require a marketplace view instance")

        if not hasattr(self, "get_value_only"):
            self.get_value_only = get_value_only
        self._latest_listing_description: str | None = None
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def build_inventory_payload(self) -> Dict[str, Any]:
        """Return the full payload expected by eBay inventory item endpoints."""

        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            raise ValueError("Remote product missing local instance for payload build")

        language_code = self._get_language_code()
        translation = self._get_translation(language_code=language_code)
        title, subtitle, description, listing_description = self._extract_content(
            translation=translation,
            language_code=language_code,
        )

        aspects = self._build_aspects(language_code=language_code)
        internal_roots: Dict[str, Any] = {}
        product_section: Dict[str, Any] = {}
        self._apply_internal_properties(
            product_section=product_section,
            root_section=internal_roots,
            language_code=language_code,
        )

        image_urls = self._collect_image_urls(product=product)

        if image_urls:
            product_section["image_urls"] = image_urls

        ean_value = self._get_ean_value()
        if ean_value:
            product_section["ean"] = ean_value

        if title:
            product_section["title"] = title[:80]
        if subtitle:
            product_section["subtitle"] = subtitle[:80]
        if description:
            product_section["description"] = description
        if language_code:
            product_section["locale"] = language_code.replace("_", "-")
        if aspects:
            product_section["aspects"] = aspects

        payload: Dict[str, Any] = {
            "sku": self._get_sku(product=product),
            "availability": {
                "ship_to_location_availability": {
                    "quantity": self._get_quantity(),
                }
            },
        }

        if product_section:
            payload["product"] = product_section

        if internal_roots:
            payload.update(internal_roots)

        self._latest_listing_description = listing_description or description
        return payload

    # ------------------------------------------------------------------
    # Configurable helpers
    # ------------------------------------------------------------------
    def is_configurable_parent(self) -> bool:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            return False
        is_configurable = getattr(product, "is_configurable", None)
        if callable(is_configurable):
            return bool(is_configurable())
        return False

    def get_parent_remote_sku(self) -> str:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            return self.remote_product.remote_sku
        return product.sku

    def get_child_remote_skus(self) -> List[str]:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None or not self.is_configurable_parent():
            return []

        child_qs = getattr(product, "children", None)
        if callable(child_qs):  # configurable product proxy
            child_products = list(child_qs())
        else:
            try:
                from products.models import ConfigurableVariation

                child_products = list(
                    ConfigurableVariation.objects.filter(parent=product)
                    .select_related("variation")
                    .values_list("variation__sku", flat=True)
                )
            except Exception:  # pragma: no cover - fallback if relation missing
                child_products = []

        if not child_products:
            return []

        return [sku for sku in child_products if sku]

    def _build_inventory_group_payload(self) -> Dict[str, Any]:
        base_payload = self.build_inventory_payload()
        product_section = base_payload.get("product", {})
        product = getattr(self.remote_product, "local_instance", None)

        variant_skus = self.get_child_remote_skus()
        varies_by = self._build_varies_by_configuration(product=product)

        group_payload: Dict[str, Any] = {
            "description": product_section.get("description"),
            "image_urls": product_section.get("image_urls", []),
            "inventory_item_group_key": self.get_parent_remote_sku(),
            "subtitle": product_section.get("subtitle"),
            "title": product_section.get("title"),
            "variant_skus": variant_skus,
            "aspects": product_section.get("aspects"),
        }

        if varies_by:
            group_payload["varies_by"] = varies_by

        base_payload.pop("sku", None)
        if "product" in base_payload:
            del base_payload["product"]
        base_payload.update(group_payload)
        return base_payload

    def _build_varies_by_configuration(self, *, product) -> Dict[str, Any] | None:
        if product is None:
            return None

        variation_data = self._collect_variation_dimensions(product=product)
        if not variation_data:
            return None

        aspects = sorted({name for name, _ in variation_data})
        specs: List[Dict[str, Any]] = []
        for name in aspects:
            values = sorted({value for aspect, value in variation_data if aspect == name})
            if values:
                specs.append({"name": name, "values": values})

        if not specs:
            return None

        return {
            "aspects_image_varies_by": aspects,
            "specifications": specs,
        }

    def _collect_variation_dimensions(self, *, product) -> List[Tuple[str, str]]:
        try:
            from products.models import ConfigurableVariation
        except ImportError:  # pragma: no cover
            return []

        mappings = ConfigurableVariation.objects.filter(parent=product).select_related("variation")
        if not mappings:
            return []

        variation_properties = (
            product.get_configurator_properties()
            if hasattr(product, "get_configurator_properties")
            else []
        )

        collected: List[Tuple[str, str]] = []
        for mapping in mappings:
            variation = getattr(mapping, "variation", None)
            if variation is None:
                continue
            for prop in variation_properties:
                prop_value = variation.get_property_value(prop)
                if prop_value in (None, ""):
                    continue
                collected.append((prop.name, str(prop_value)))
        return collected

    def get_listing_description(self) -> str | None:
        """Expose the last computed listing description for offer updates."""

        return self._latest_listing_description

    def serialize_response(self, response: Any) -> Any:  # pragma: no cover - thin wrapper
        return True if response is None else response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_language_code(self) -> str | None:
        language = None
        remote_languages = getattr(self.view, "remote_languages", None)
        if remote_languages is not None:
            remote_language = remote_languages.first()
            if remote_language and remote_language.local_instance:
                language = remote_language.local_instance
        if language:
            return language
        return getattr(self.sales_channel.multi_tenant_company, "language", None)

    def _get_translation(self, *, language_code: str | None) -> ProductTranslation | None:
        product = self.remote_product.local_instance
        if language_code is None:
            return ProductTranslation.objects.filter(
                product=product,
                sales_channel=None,
            ).first()

        channel_translation = ProductTranslation.objects.filter(
            product=product,
            language=language_code,
            sales_channel=self.sales_channel,
        ).first()
        if channel_translation:
            return channel_translation

        return ProductTranslation.objects.filter(
            product=product,
            language=language_code,
            sales_channel=None,
        ).first()

    def _extract_content(
        self,
        *,
        translation: ProductTranslation | None,
        language_code: str | None,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        product = self.remote_product.local_instance
        default_translation = None
        if translation and translation.sales_channel_id:
            default_translation = ProductTranslation.objects.filter(
                product=product,
                language=translation.language,
                sales_channel=None,
            ).first()
        elif translation:
            default_translation = translation

        title = None
        subtitle = None
        description = None
        listing_description = None

        if translation:
            title = translation.name or None
            subtitle = translation.subtitle or None
            description = translation.description or translation.short_description or None
            listing_description = translation.short_description or translation.description or None

        if not title and default_translation:
            title = default_translation.name or None
        if not subtitle and default_translation:
            subtitle = default_translation.subtitle or None
        if not description and default_translation:
            description = default_translation.description or default_translation.short_description or None
        if not listing_description and default_translation:
            listing_description = (
                default_translation.short_description
                or default_translation.description
                or None
            )

        if not title:
            title = getattr(product, "name", None)
        if not description:
            description = getattr(product, "description", None)

        return title, subtitle, description, listing_description

    def _collect_image_urls(self, *, product) -> List[str]:
        throughs = (
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=self.sales_channel,
            )
            .filter(media__type=Media.IMAGE)
            .order_by("sort_order")
        )

        urls: List[str] = []
        for through in throughs:
            media = through.media
            if media and media.image_web_url:
                urls.append(media.image_web_url)
        return urls

    def _get_ean_value(self) -> str | None:
        if getattr(self, "_ean_factory_marker", False):
            value = getattr(self, "_ean_value", None)
            return value or None

        factory_class = getattr(self, "remote_eancode_update_factory", None)
        if factory_class is None or not getattr(self, "remote_product", None):
            return None

        remote_instance = factory_class.remote_model_class.objects.filter(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        ).first()

        factory_kwargs: Dict[str, Any] = {
            "sales_channel": self.sales_channel,
            "local_instance": self.remote_product.local_instance,
            "remote_product": self.remote_product,
            "view": self.view,
            "get_value_only": True,
        }

        if remote_instance is not None:
            factory_kwargs["remote_instance"] = remote_instance

        factory = factory_class(**factory_kwargs)
        if factory.get_value_only and getattr(factory, "api", None) is None:
            sentinel = getattr(self, "api", None)
            factory.api = sentinel if sentinel is not None else object()

        value = factory.run()
        return value or None

    def _get_sku(self, *, product) -> str:
        if getattr(self.remote_product, "remote_sku", None):
            return self.remote_product.remote_sku
        return product.sku

    def _get_quantity(self) -> int:
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock is None:
            return 0

        product = getattr(self.remote_product, "local_instance", None)
        if product is not None:
            if not getattr(product, "active", True):
                return 0

            is_configurable = getattr(product, "is_configurable", None)
            if callable(is_configurable) and is_configurable():
                return 0

        return max(int(starting_stock), 0)

    def _build_aspects(self, *, language_code: str | None) -> Dict[str, List[str]]:
        product = self.remote_product.local_instance
        product_properties = {
            prop.property_id: prop
            for prop in ProductProperty.objects.filter(product=product)
        }

        if not product_properties:
            return {}

        queryset = (
            EbayProperty.objects.filter(sales_channel=self.sales_channel)
            .filter(Q(marketplace=self.view) | Q(marketplace__isnull=True))
            .select_related("local_instance")
        )

        aspects: Dict[str, List[str]] = {}
        for remote_property in queryset:
            local_property = remote_property.local_instance
            if not local_property:
                continue
            product_property = product_properties.get(local_property.id)
            if not product_property:
                continue

            values = self._render_property_value(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )
            if not values:
                continue

            name = (
                remote_property.localized_name
                or remote_property.translated_name
                or remote_property.remote_id
            )
            if not name:
                continue

            if isinstance(values, str):
                values_list = [values]
            else:
                values_list = [str(value) for value in values if value not in (None, "")]
            if not values_list:
                continue
            aspects[name] = values_list
        return aspects

    def _apply_internal_properties(
        self,
        *,
        product_section: Dict[str, Any],
        root_section: Dict[str, Any],
        language_code: str | None,
    ) -> None:
        product = self.remote_product.local_instance
        product_properties = {
            prop.property_id: prop
            for prop in ProductProperty.objects.filter(product=product)
        }
        if not product_properties:
            return

        internal_properties = (
            EbayInternalProperty.objects.filter(sales_channel=self.sales_channel)
            .select_related("local_instance")
        )

        for internal_property in internal_properties:
            local_property = internal_property.local_instance
            if not local_property:
                continue
            product_property = product_properties.get(local_property.id)
            if not product_property:
                continue

            value = self._render_basic_property_value(
                product_property=product_property,
                language_code=language_code,
            )
            if value in (None, "", []):
                continue

            target = root_section if internal_property.is_root else product_section
            self._assign_nested_value(container=target, path=internal_property.code, value=value)

    def _render_property_value(
        self,
        *,
        product_property: ProductProperty,
        remote_property: EbayProperty,
        language_code: str | None,
    ) -> Any:
        local_property = product_property.property
        if local_property.type == Property.TYPES.SELECT:
            select_value = product_property.value_select
            if select_value is None:
                return None
            remote_value = EbayPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=remote_property.marketplace,
                ebay_property=remote_property,
                local_instance=select_value,
            ).first()
            if remote_value:
                return remote_value.localized_value or remote_value.translated_value or remote_value.remote_id
            return select_value.value(language_code)

        if local_property.type == Property.TYPES.MULTISELECT:
            values: List[str] = []
            for select_value in product_property.value_multi_select.all():
                remote_value = EbayPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    marketplace=remote_property.marketplace,
                    ebay_property=remote_property,
                    local_instance=select_value,
                ).first()
                if remote_value and (remote_value.localized_value or remote_value.translated_value):
                    values.append(remote_value.localized_value or remote_value.translated_value)
                else:
                    values.append(select_value.value(language_code))
            filtered = [value for value in values if value not in (None, "")]
            return filtered or None

        value = product_property.get_serialised_value(language=language_code)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            filtered = [str(entry) for entry in value if entry not in (None, "")]
            return filtered or None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if value in (None, ""):
            return None
        return str(value)

    def _render_basic_property_value(
        self,
        *,
        product_property: ProductProperty,
        language_code: str | None,
    ) -> Any:
        property_type = product_property.property.type
        if property_type == Property.TYPES.SELECT:
            select_value = product_property.value_select
            if select_value is None:
                return None
            return select_value.value(language_code)
        if property_type == Property.TYPES.MULTISELECT:
            values = [value.value(language_code) for value in product_property.value_multi_select.all()]
            filtered = [value for value in values if value not in (None, "")]
            return filtered or None
        value = product_property.get_serialised_value(language=language_code)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            filtered = [entry for entry in value if entry not in (None, "")]
            return filtered or None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    def _assign_nested_value(self, *, container: Dict[str, Any], path: str, value: Any) -> None:
        if not path:
            return
        parts = path.split("__")
        current = container
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def _prepare_property_remote_value(self, *, product_property: ProductProperty, remote_property: EbayProperty | None) -> str:
        language_code = self._get_language_code()
        if remote_property is not None:
            value = self._render_property_value(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )
        else:
            value = self._render_basic_property_value(
                product_property=product_property,
                language_code=language_code,
            )
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        if value is None:
            return ""
        return str(value)

    def _get_offer_remote_id(self) -> str | None:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None or self.view is None:
            return None
        assign = (
            SalesChannelViewAssign.objects.filter(
                product=product,
                sales_channel_view=self.view,
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .first()
        )
        return assign.remote_id if assign else None

    def _get_content_language(self) -> str:
        language_code = self._get_language_code()
        if language_code:
            return language_code.replace("_", "-")
        return "en-US"


class EbayInventoryItemPushMixin(EbayInventoryItemPayloadMixin):
    """Mixin adding API submission helpers for inventory payloads."""

    def __init__(self, *args: Any, view=None, get_value_only: bool = False, **kwargs: Any) -> None:
        if view is None:
            raise ValueError("Ebay factories require a marketplace view instance")

        self.view = view
        if "get_value_only" not in kwargs:
            kwargs["get_value_only"] = get_value_only
        self.get_value_only = kwargs["get_value_only"]
        super().__init__(*args, **kwargs)

    def send_inventory_payload(self) -> Any:
        is_parent = self.is_configurable_parent()
        payload = (
            self._build_inventory_group_payload()
            if is_parent
            else self.build_inventory_payload()
        )

        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api

        if is_parent:
            return api.sell_inventory_create_or_replace_inventory_item_group(
                body=payload,
                content_language=self._get_content_language(),
                content_type="application/json",
                inventory_item_group_key=self.get_parent_remote_sku(),
            )

        return api.sell_inventory_create_or_replace_inventory_item(
            body=payload,
            content_language=self._get_content_language(),
            content_type="application/json",
        )


class EbayProductPropertyValueMixin(EbayInventoryItemPushMixin):
    """Shared helpers for eBay product property factories."""

    remote_model_class = EbayProductProperty

    def _compute_remote_value(self, *, remote_property: EbayProperty | None) -> str:
        return self._prepare_property_remote_value(
            product_property=self.local_instance,
            remote_property=remote_property,
        )
