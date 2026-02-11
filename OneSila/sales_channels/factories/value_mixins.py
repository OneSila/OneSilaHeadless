from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Any, Optional

from properties.models import ProductPropertyTextTranslation, Property
from sales_channels.exceptions import PreFlightCheckError


class RemoteValueMixin:
    """Shared conversion flow for translating local ProductProperty values to remote values."""

    def get_remote_value(
        self,
        *,
        product_property=None,
        remote_property=None,
        language_code: Optional[str] = None,
    ):
        local_property = self.get_local_property(product_property=product_property)
        if local_property is None:
            return None

        property_type = self.get_property_type(local_property=local_property, remote_property=remote_property)
        value = self.get_property_value(
            product_property=product_property,
            local_property=local_property,
            remote_property=remote_property,
            language_code=language_code,
        )

        if property_type == Property.TYPES.INT:
            return self.get_int_value(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.FLOAT:
            return self.get_float_value(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.BOOLEAN:
            return self.get_boolean_value(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.SELECT:
            return self.get_select_value(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.MULTISELECT:
            return self.get_select_value_multiple(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.TEXT:
            return self.get_text_value(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.DESCRIPTION:
            return self.get_description_value(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.DATE:
            return self.format_date(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        if property_type == Property.TYPES.DATETIME:
            return self.format_datetime(
                value=value,
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )

        return None

    def get_local_property(self, *, product_property=None):
        prop_instance = product_property or getattr(self, "local_instance", None)
        if prop_instance is None:
            return getattr(self, "local_property", None)
        return getattr(prop_instance, "property", None) or getattr(self, "local_property", None)

    def get_property_type(self, *, local_property, remote_property=None):
        _ = remote_property
        return getattr(local_property, "type", None)

    def get_property_value(
        self,
        *,
        product_property=None,
        local_property=None,
        remote_property=None,
        language_code: Optional[str] = None,
    ):
        _ = local_property
        _ = remote_property
        prop_instance = product_property or getattr(self, "local_instance", None)
        if prop_instance is None:
            return None

        get_value = getattr(prop_instance, "get_value", None)
        if callable(get_value):
            try:
                return get_value(language=language_code)
            except TypeError:
                return get_value()

        return None

    def get_int_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = product_property
        _ = remote_property
        _ = language_code
        return value

    def _remote_property_label(self, *, product_property=None, remote_property=None):
        if remote_property is not None:
            for attribute in [
                "name",
                "localized_name",
                "translated_name",
                "name_en",
                "code",
                "attribute_code",
                "remote_id",
            ]:
                label = getattr(remote_property, attribute, None)
                if label not in (None, ""):
                    return str(label)

        local_property = self.get_local_property(product_property=product_property)
        if local_property is not None:
            name = getattr(local_property, "name", None)
            internal_name = getattr(local_property, "internal_name", None)
            if name not in (None, ""):
                return str(name)
            if internal_name not in (None, ""):
                return str(internal_name)
        return "Unknown property"

    def get_float_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = product_property
        _ = language_code
        if remote_property and (
            getattr(remote_property, "original_type", None) == Property.TYPES.INT
            and getattr(remote_property, "type", None) == Property.TYPES.FLOAT
        ):
            if value is None:
                return None
            try:
                decimal_value = Decimal(str(value))
            except (InvalidOperation, TypeError, ValueError):
                label = self._remote_property_label(
                    product_property=product_property,
                    remote_property=remote_property,
                )
                raise PreFlightCheckError(
                    f"Property '{label}' expects a whole number in the integration, but received non-numeric value '{value}'."
                )

            if decimal_value == decimal_value.to_integral_value():
                return int(decimal_value)

            label = self._remote_property_label(
                product_property=product_property,
                remote_property=remote_property,
            )
            raise PreFlightCheckError(
                f"Property '{label}' expects a whole number in the integration (original INT), "
                f"but OneSila provided a decimal value '{value}'."
            )

        return value

    def get_boolean_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = product_property
        _ = remote_property
        _ = language_code
        return True if value in [True, "true", "True", "1", 1] else False

    def get_select_option_value(self, *, select_value, language_code: Optional[str] = None):
        if select_value is None:
            return None
        if language_code and hasattr(select_value, "value_by_language_code"):
            translated = select_value.value_by_language_code(language=language_code)
            if translated not in (None, ""):
                return translated
        return getattr(select_value, "value", None)

    def get_select_values_local(self, *, product_property=None, multiple: bool):
        prop_instance = product_property or getattr(self, "local_instance", None)
        if prop_instance is None:
            return []

        if multiple:
            manager = getattr(prop_instance, "value_multi_select", None)
            if manager is None:
                return []
            return list(manager.all())

        select_value = getattr(prop_instance, "value_select", None)
        return [select_value] if select_value else []

    def get_select_value_local(
        self,
        *,
        product_property=None,
        multiple: bool,
        language_code: Optional[str] = None,
    ):
        values = self.get_select_values_local(product_property=product_property, multiple=multiple)
        resolved = [
            self.get_select_option_value(select_value=value, language_code=language_code)
            for value in values
            if value is not None
        ]
        filtered = [entry for entry in resolved if entry not in (None, "")]
        if multiple:
            return filtered
        return filtered[0] if filtered else None

    def get_select_value(self, *, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = remote_property
        return self.get_select_value_local(
            product_property=product_property,
            multiple=False,
            language_code=language_code,
        )

    def get_select_value_multiple(self, *, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = remote_property
        return self.get_select_value_local(
            product_property=product_property,
            multiple=True,
            language_code=language_code,
        )

    def get_text_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = remote_property
        return self.get_translated_values(
            product_property=product_property,
            language_code=language_code,
            fallback_value=value,
        )

    def get_description_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = remote_property
        return self.get_translated_values(
            product_property=product_property,
            language_code=language_code,
            fallback_value=value,
        )

    def get_translated_values(self, *, product_property=None, language_code: Optional[str] = None, fallback_value=None):
        _ = language_code
        prop_instance = product_property or getattr(self, "local_instance", None)
        local_property = self.get_local_property(product_property=product_property)
        if prop_instance is None or local_property is None:
            return fallback_value

        if local_property.type not in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION]:
            return fallback_value

        default_translation = ProductPropertyTextTranslation.objects.filter(product_property=prop_instance).first()
        if not default_translation:
            return fallback_value

        if local_property.type == Property.TYPES.TEXT:
            return default_translation.value_text
        return default_translation.value_description

    def format_date(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = product_property
        _ = remote_property
        _ = language_code
        return value.isoformat()[:10] if isinstance(value, (date, datetime)) else None

    def format_datetime(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = product_property
        _ = remote_property
        _ = language_code
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time()).isoformat()
        return None
