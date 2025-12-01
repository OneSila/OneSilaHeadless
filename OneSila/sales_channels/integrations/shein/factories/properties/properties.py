from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Iterable, Optional, Sequence

from properties.models import ProductProperty, Property
from sales_channels.exceptions import PreFlightCheckError, RemotePropertyValueNotMapped
from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyDeleteFactory,
    RemoteProductPropertyUpdateFactory,
)
from sales_channels.models.properties import RemoteProductProperty

from sales_channels.integrations.shein.models import (
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteLanguage,
)


class SheinRemotePropertyEnsureFactory:
    """Guard rail enforcing that Shein properties are imported and mapped before push."""

    remote_model_class = SheinProperty

    def __init__(self, sales_channel, local_instance, api=None, **kwargs):
        self.sales_channel = sales_channel
        self.local_instance = local_instance
        self.api = api
        self.remote_instance = None

    def run(self):  # pragma: no cover - defensive path
        raise PreFlightCheckError(
            "Import Shein attributes and map them locally before syncing product properties."
        )


class SheinRemotePropertySelectValueEnsureFactory:
    """Guard rail enforcing that Shein attribute values are mapped."""

    remote_model_class = SheinPropertySelectValue

    def __init__(self, sales_channel, local_instance, api=None, **kwargs):
        self.sales_channel = sales_channel
        self.local_instance = local_instance
        self.api = api
        self.remote_instance = None

    def run(self):  # pragma: no cover - defensive path
        raise PreFlightCheckError(
            "Import Shein attribute values and map them locally before syncing product properties."
        )


class SheinProductPropertyValueMixin:
    """Shared helpers to render Shein-ready attribute payloads."""

    remote_property_factory = SheinRemotePropertyEnsureFactory
    remote_property_select_value_factory = SheinRemotePropertySelectValueEnsureFactory

    def get_api(self):
        return getattr(self, "api", None)

    def _normalize_identifier(self, *, value: Any) -> Optional[int | str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text)
        except (TypeError, ValueError):
            return text

    def _normalize_language(self) -> Optional[str]:
        if self.language is None:
            return None

        if isinstance(self.language, SheinRemoteLanguage):
            return self.language.remote_code or self.language.local_instance

        if hasattr(self.language, "language"):
            return getattr(self.language, "language")

        text = str(self.language).strip()
        return text or None

    def _clean_payload(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if value not in (None, "", [], {})
        }

    def _coerce_basic_value(
        self,
        *,
        product_property: ProductProperty,
        language_code: Optional[str],
    ) -> Any:
        prop_type = product_property.property.type
        value = product_property.get_value(language=language_code)

        if value in (None, "", []):
            return None

        if prop_type == Property.TYPES.DATE:
            return value.isoformat() if isinstance(value, date) else None

        if prop_type == Property.TYPES.DATETIME:
            return value.isoformat() if isinstance(value, datetime) else None

        if prop_type == Property.TYPES.BOOLEAN:
            return bool(value)

        if prop_type == Property.TYPES.INT:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        if prop_type == Property.TYPES.FLOAT:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        return value

    def _collect_select_payload(
        self,
        *,
        product_property: ProductProperty,
        shein_property: SheinProperty,
        allow_custom_values: bool,
        language_code: Optional[str],
    ) -> tuple[list[Any], list[str]]:
        if product_property.property.type == Property.TYPES.MULTISELECT:
            local_values: Iterable = product_property.value_multi_select.all()
        else:
            local_values = [product_property.value_select] if product_property.value_select else []

        remote_ids: list[Any] = []
        custom_values: list[str] = []

        for value in local_values:
            if not value:
                continue

            remote_val = SheinPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=shein_property,
                local_instance=value,
            ).first()

            if remote_val:
                normalized = self._normalize_identifier(value=remote_val.remote_id)
                if normalized is not None:
                    remote_ids.append(normalized)
                continue

            if not allow_custom_values:
                prop_label = shein_property.name or shein_property.name_en or shein_property.remote_id
                local_label = value.value_by_language_code(language=language_code) or value.value
                raise RemotePropertyValueNotMapped(
                    f"Value '{local_label}' for Shein property '{prop_label}' is not mapped and custom values are not allowed."
                )

            translated_value = value.value_by_language_code(language=language_code) or value.value
            if translated_value not in (None, ""):
                custom_values.append(str(translated_value))

        return remote_ids, custom_values

    def _resolve_product_type_item(self, *, fallback: Optional[Sequence[SheinProductTypeItem]] = None) -> SheinProductTypeItem:
        if getattr(self, "product_type_item", None) is not None:
            return self.product_type_item

        candidates = list(
            (fallback or [])
        ) or list(
            SheinProductTypeItem.objects.filter(
                property=getattr(self.remote_instance, "remote_property", None),
                sales_channel=self.sales_channel,
            )
        )

        if len(candidates) == 1:
            return candidates[0]

        raise PreFlightCheckError(
            "Provide the Shein product type item to build the attribute payload."
        )

    def _build_remote_value(
        self,
        *,
        product_property: ProductProperty,
        product_type_item: SheinProductTypeItem,
    ) -> dict[str, Any]:
        shein_property = product_type_item.property
        if shein_property is None:
            raise PreFlightCheckError("Shein property is required to build attribute payload.")

        attribute_id = self._normalize_identifier(value=shein_property.remote_id)
        if attribute_id is None:
            raise PreFlightCheckError("Shein property is missing a remote_id mapping.")

        if shein_property.local_instance and shein_property.local_instance != product_property.property:
            raise PreFlightCheckError("Mapped Shein property does not match the product property being synced.")

        language_code = self._normalize_language()
        allow_custom_values = bool(
            shein_property.allows_unmapped_values and product_type_item.allows_unmapped_values
        )

        attribute_value_id: Any = None
        attribute_extra_value: Any = None
        custom_attribute_value: Any = None

        if product_property.property.type in (Property.TYPES.SELECT, Property.TYPES.MULTISELECT):
            remote_ids, custom_values = self._collect_select_payload(
                product_property=product_property,
                shein_property=shein_property,
                allow_custom_values=allow_custom_values,
                language_code=language_code,
            )

            if product_property.property.type == Property.TYPES.SELECT:
                attribute_value_id = remote_ids[0] if remote_ids else None
                if custom_values:
                    attribute_extra_value = custom_values[0]
                    if product_type_item.attribute_type == SheinProductTypeItem.AttributeType.SALES:
                        custom_attribute_value = custom_values[0]
            else:
                attribute_value_id = remote_ids
                if custom_values:
                    attribute_extra_value = custom_values
                    if product_type_item.attribute_type == SheinProductTypeItem.AttributeType.SALES:
                        custom_attribute_value = custom_values

        else:
            attribute_extra_value = self._coerce_basic_value(
                product_property=product_property,
                language_code=language_code,
            )

        payload = self._clean_payload(
            payload={
                "attribute_id": attribute_id,
                "attribute_type": product_type_item.attribute_type,
                "attribute_value_id": attribute_value_id,
                "attribute_extra_value": attribute_extra_value,
                "custom_attribute_value": custom_attribute_value,
                "language": language_code,
            }
        )

        return payload

    def _render_remote_value(self, *, payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True)


class SheinProductPropertyCreateFactory(
    SheinProductPropertyValueMixin,
    RemoteProductPropertyCreateFactory,
):
    """Compute Shein attribute payloads for new product property mirrors."""

    remote_model_class = RemoteProductProperty

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        *,
        product_type_item: SheinProductTypeItem,
        api=None,
        skip_checks: bool = False,
        get_value_only: bool = False,
        language=None,
    ):
        self.product_type_item = product_type_item
        self.remote_property = getattr(product_type_item, "property", None)
        super().__init__(
            sales_channel,
            local_instance,
            remote_product=remote_product,
            api=api,
            skip_checks=skip_checks,
            get_value_only=get_value_only,
            language=language,
        )

    def preflight_check(self):
        if self.get_value_only:
            return True
        return super().preflight_check()

    def preflight_process(self):
        remote_payload = self._build_remote_value(
            product_property=self.local_instance,
            product_type_item=self.product_type_item,
        )
        self.remote_value = self._render_remote_value(payload=remote_payload)

    def create_remote(self):
        return {}

    def serialize_response(self, response):
        return response


class SheinProductPropertyUpdateFactory(
    SheinProductPropertyValueMixin,
    RemoteProductPropertyUpdateFactory,
):
    """Update Shein attribute payload mirrors."""

    remote_model_class = RemoteProductProperty
    create_factory_class = SheinProductPropertyCreateFactory

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        *,
        product_type_item: Optional[SheinProductTypeItem] = None,
        api=None,
        get_value_only: bool = False,
        remote_instance=None,
        skip_checks: bool = False,
        language=None,
    ):
        self.product_type_item = product_type_item
        super().__init__(
            sales_channel,
            local_instance,
            remote_product=remote_product,
            api=api,
            get_value_only=get_value_only,
            remote_instance=remote_instance,
            skip_checks=skip_checks,
            language=language,
        )

    def get_remote_value(self):
        fallback_items: Sequence[SheinProductTypeItem] = ()
        remote_prop = getattr(self.remote_instance, "remote_property", None)
        if remote_prop and hasattr(remote_prop, "product_type_items"):
            fallback_items = remote_prop.product_type_items.filter(sales_channel=self.sales_channel)

        product_type_item = self._resolve_product_type_item(fallback=fallback_items)

        remote_payload = self._build_remote_value(
            product_property=self.local_instance,
            product_type_item=product_type_item,
        )
        self.remote_value = self._render_remote_value(payload=remote_payload)
        return self.remote_value

    def serialize_response(self, response):
        return response


class SheinProductPropertyDeleteFactory(RemoteProductPropertyDeleteFactory):
    """Delete the local mirror for a Shein product property without remote API calls."""

    remote_model_class = RemoteProductProperty

    def delete_remote(self):
        return True

    def serialize_response(self, response):
        return True
