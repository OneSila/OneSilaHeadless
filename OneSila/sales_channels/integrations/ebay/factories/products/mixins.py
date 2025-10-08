from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
import json
from typing import Any, Dict, List

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
        payload = self.build_inventory_payload()
        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
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
