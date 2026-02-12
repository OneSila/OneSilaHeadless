from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Any, Optional

from properties.models import Property
from sales_channels.constants import REMOTE_PROPERTY_TYPE_CHANGE_RULES
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

        self.validate_remote_mapping_compatibility(
            product_property=product_property,
            remote_property=remote_property,
        )

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
        _ = language_code
        if value is None:
            return None

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        match (original_type, target_type):
            case (Property.TYPES.FLOAT, Property.TYPES.INT):
                return float(value)

            case _:
                return self._coerce_int_value_for_textual_original(
                    value=value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

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

    def _raise_value_expectation_preflight_error(
        self,
        *,
        product_property=None,
        remote_property=None,
        expected_description: str,
        provided_description: str,
        provided_value,
    ):
        label = self._remote_property_label(
            product_property=product_property,
            remote_property=remote_property,
        )
        raise PreFlightCheckError(
            f"Property '{label}' expects {expected_description} in the integration, "
            f"but OneSila provided {provided_description} '{provided_value}'."
        )

    def _resolve_remote_mapping_rule_key(self, *, remote_property):
        original_type = getattr(remote_property, "original_type", None)
        if original_type == Property.TYPES.SELECT:
            allows_unmapped_values = bool(getattr(remote_property, "allows_unmapped_values", False))
            return "SELECT__allows_custom_values" if allows_unmapped_values else "SELECT__not_allows_custom_values"
        if original_type == Property.TYPES.MULTISELECT:
            allows_unmapped_values = bool(getattr(remote_property, "allows_unmapped_values", False))
            return "MULTISELECT__allows_custom_values" if allows_unmapped_values else "MULTISELECT__not_allows_custom_values"
        return original_type

    def validate_remote_mapping_compatibility(self, *, product_property=None, remote_property=None):
        if remote_property is None:
            return

        original_type = getattr(remote_property, "original_type", None)
        target_type = getattr(remote_property, "type", None)
        if original_type in (None, "") or target_type in (None, ""):
            return

        rule_key = self._resolve_remote_mapping_rule_key(remote_property=remote_property)
        allowed_targets = REMOTE_PROPERTY_TYPE_CHANGE_RULES.get(rule_key, {})
        if bool(allowed_targets.get(target_type)):
            return

        label = self._remote_property_label(
            product_property=product_property,
            remote_property=remote_property,
        )
        raise PreFlightCheckError(
            f"Property '{label}' is mapped to a non-compatible type ({original_type} -> {target_type})."
        )

    def _resolve_original_and_target_types(self, *, product_property=None, remote_property=None):
        local_property = self.get_local_property(product_property=product_property)
        local_type = getattr(local_property, "type", None)

        if remote_property is None:
            return local_type, local_type

        original_type = getattr(remote_property, "original_type", None) or local_type
        target_type = getattr(remote_property, "type", None) or local_type
        return original_type, target_type

    def _parse_decimal_value(self, *, value):
        if value in (None, ""):
            return None

        normalized = str(value).strip().replace(",", ".")
        if normalized == "":
            return None

        try:
            return Decimal(normalized)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _coerce_float_textual_value(
        self,
        *,
        translated_value,
        product_property=None,
        remote_property=None,
        provided_description: str,
    ):
        decimal_value = self._parse_decimal_value(value=translated_value)
        if decimal_value is not None:
            return float(decimal_value)

        self._raise_value_expectation_preflight_error(
            product_property=product_property,
            remote_property=remote_property,
            expected_description="a numeric value",
            provided_description=provided_description,
            provided_value=translated_value,
        )

    def get_float_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = language_code
        if value is None:
            return None

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )

        match (original_type, target_type):
            case (Property.TYPES.FLOAT, Property.TYPES.FLOAT):
                return self._coerce_float_value_for_textual_original(
                    value=value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case (Property.TYPES.INT, Property.TYPES.FLOAT):
                try:
                    decimal_value = Decimal(str(value))
                except (InvalidOperation, TypeError, ValueError):
                    decimal_value = None

                if decimal_value is not None and decimal_value == decimal_value.to_integral_value():
                    return int(decimal_value)

                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a whole number",
                    provided_description="a decimal value",
                    provided_value=value,
                )

            case ((Property.TYPES.SELECT | Property.TYPES.MULTISELECT), Property.TYPES.FLOAT):
                decimal_value = self._parse_decimal_value(value=value)
                if decimal_value is not None:
                    return float(decimal_value)
                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a numeric value",
                    provided_description="a non-numeric value",
                    provided_value=value,
                )

            case _:
                coerced = self._coerce_float_value_for_textual_original(
                    value=value,
                    product_property=product_property,
                    remote_property=remote_property,
                )
                if coerced is not value:
                    return coerced
                label = self._remote_property_label(
                    product_property=product_property,
                    remote_property=remote_property,
                )
                raise PreFlightCheckError(
                    f"Property '{label}' is mapped to a non-compatible type ({original_type} -> {target_type}) for float conversion."
                )

    def get_boolean_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = language_code
        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        desired_bool = value in [True, "true", "True", "1", 1]
        match (original_type, target_type):
            case (Property.TYPES.TEXT, Property.TYPES.BOOLEAN) | (Property.TYPES.DESCRIPTION, Property.TYPES.BOOLEAN):
                if remote_property is not None:
                    yes_text = getattr(remote_property, "yes_text_value", None) or "Yes"
                    no_text = getattr(remote_property, "no_text_value", None) or "No"
                else:
                    yes_text = "Yes"
                    no_text = "No"
                return yes_text if desired_bool else no_text

            case ((Property.TYPES.SELECT | Property.TYPES.MULTISELECT), Property.TYPES.BOOLEAN):
                mapped_value = self._resolve_boolean_select_mapped_value(
                    remote_property=remote_property,
                    desired_bool=desired_bool,
                )
                if mapped_value not in (None, ""):
                    return mapped_value

                if self._is_select_like_without_custom_values(remote_property=remote_property):
                    label = self._remote_property_label(
                        product_property=product_property,
                        remote_property=remote_property,
                    )
                    raise PreFlightCheckError(
                        f"Property '{label}' is mapped to boolean and requires explicit select option mappings "
                        "with bool_value=True/False."
                    )

                if remote_property is not None and getattr(remote_property, "allows_unmapped_values", False):
                    yes_text = getattr(remote_property, "yes_text_value", None)
                    no_text = getattr(remote_property, "no_text_value", None)
                    if desired_bool and yes_text not in (None, ""):
                        return yes_text
                    if not desired_bool and no_text not in (None, ""):
                        return no_text
                return desired_bool

            case (Property.TYPES.BOOLEAN, Property.TYPES.BOOLEAN):
                return desired_bool

            case _:
                return desired_bool

    def _is_select_like_without_custom_values(self, *, remote_property=None) -> bool:
        if remote_property is None:
            return False
        return self._resolve_remote_mapping_rule_key(remote_property=remote_property) in {
            "SELECT__not_allows_custom_values",
            "MULTISELECT__not_allows_custom_values",
        }

    def _get_remote_property_select_values_queryset(self, *, remote_property=None):
        if remote_property is None:
            return None

        for related_name in ("select_values", "sheinpropertyselectvalue_set", "remotepropertyselectvalue_set"):
            manager = getattr(remote_property, related_name, None)
            if manager is not None and hasattr(manager, "all"):
                queryset = manager.all()
                model = getattr(queryset, "model", None)
                if model is not None and hasattr(model, "marketplace_id"):
                    view = getattr(self, "view", None)
                    if view is not None and hasattr(view, "id"):
                        queryset = queryset.filter(marketplace=view)
                return queryset

        return None

    def _extract_remote_select_boolean_value(self, *, remote_select_value):
        for field_name in ("remote_value", "localized_value", "remote_id", "value", "value_en", "translated_value"):
            candidate = getattr(remote_select_value, field_name, None)
            if candidate not in (None, ""):
                return candidate
        return None

    def _resolve_boolean_select_mapped_value(self, *, remote_property=None, desired_bool: bool):
        queryset = self._get_remote_property_select_values_queryset(remote_property=remote_property)
        if queryset is None:
            return None

        mapped_value = queryset.filter(bool_value=desired_bool).first()
        if mapped_value is None:
            return None

        return self._extract_remote_select_boolean_value(remote_select_value=mapped_value)

    def _is_textual_original_type(self, *, product_property=None, remote_property=None) -> bool:
        original_type, _ = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        return original_type in (Property.TYPES.TEXT, Property.TYPES.DESCRIPTION)

    def _is_textual_or_numeric_original_type(self, *, product_property=None, remote_property=None) -> bool:
        original_type, _ = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        return original_type in (
            Property.TYPES.TEXT,
            Property.TYPES.DESCRIPTION,
            Property.TYPES.INT,
            Property.TYPES.FLOAT,
        )

    def _coerce_select_value_for_original_type(
        self,
        *,
        selected_value,
        product_property=None,
        remote_property=None,
    ):
        if selected_value in (None, ""):
            return selected_value

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        if target_type != Property.TYPES.SELECT:
            return selected_value

        match original_type:
            case Property.TYPES.INT:
                decimal_value = self._parse_decimal_value(value=selected_value)
                if decimal_value is not None and decimal_value == decimal_value.to_integral_value():
                    return int(decimal_value)
                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a whole number",
                    provided_description="a non-integer select value",
                    provided_value=selected_value,
                )

            case Property.TYPES.FLOAT:
                decimal_value = self._parse_decimal_value(value=selected_value)
                if decimal_value is not None:
                    return float(decimal_value)
                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a numeric value",
                    provided_description="a non-numeric select value",
                    provided_value=selected_value,
                )

            case _:
                return selected_value

    def _coerce_multiselect_for_textual_original(
        self,
        *,
        values,
        product_property=None,
        remote_property=None,
    ):
        if not self._is_textual_original_type(
            product_property=product_property,
            remote_property=remote_property,
        ):
            return values
        if not values:
            return None
        return ",".join(str(value) for value in values)

    def _coerce_text_value_for_textual_original(
        self,
        *,
        translated_value,
        product_property=None,
        remote_property=None,
    ):
        if not self._is_textual_original_type(
            product_property=product_property,
            remote_property=remote_property,
        ):
            return translated_value
        if translated_value in (None, ""):
            return translated_value
        return str(translated_value)

    def _ensure_text_length_for_text_original(
        self,
        *,
        translated_value,
        product_property=None,
        remote_property=None,
    ):
        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        if original_type != Property.TYPES.TEXT or target_type != Property.TYPES.DESCRIPTION:
            return translated_value
        if translated_value in (None, ""):
            return translated_value
        if len(str(translated_value)) <= 255:
            return translated_value

        self._raise_value_expectation_preflight_error(
            product_property=product_property,
            remote_property=remote_property,
            expected_description="a text value with maximum length 255",
            provided_description="a longer description value",
            provided_value=translated_value,
        )

    def _coerce_int_value_for_textual_original(
        self,
        *,
        value,
        product_property=None,
        remote_property=None,
    ):
        if not self._is_textual_original_type(
            product_property=product_property,
            remote_property=remote_property,
        ):
            return value
        if value is None:
            return None
        return str(value)

    def _coerce_float_value_for_textual_original(
        self,
        *,
        value,
        product_property=None,
        remote_property=None,
    ):
        if not self._is_textual_original_type(
            product_property=product_property,
            remote_property=remote_property,
        ):
            return value
        if value is None:
            return None
        return str(value)

    def _coerce_boolean_text_for_boolean_original(
        self,
        *,
        translated_value,
        product_property=None,
        remote_property=None,
    ):
        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        if original_type != Property.TYPES.BOOLEAN or target_type not in (Property.TYPES.TEXT, Property.TYPES.DESCRIPTION):
            return translated_value

        if translated_value in (None, ""):
            return None

        yes_text = getattr(remote_property, "yes_text_value", None) if remote_property is not None else None
        no_text = getattr(remote_property, "no_text_value", None) if remote_property is not None else None
        yes_text = yes_text or "Yes"
        no_text = no_text or "No"

        normalized_value = str(translated_value).strip().lower()
        normalized_yes = str(yes_text).strip().lower()
        normalized_no = str(no_text).strip().lower()

        if normalized_value == normalized_yes:
            return True
        if normalized_value == normalized_no:
            return False

        label = self._remote_property_label(
            product_property=product_property,
            remote_property=remote_property,
        )
        raise PreFlightCheckError(
            f"Property '{label}' is mapped for a boolean integration value and accepts only "
            f"'{yes_text}' or '{no_text}', but received '{translated_value}'."
        )

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
        selected_value = self.get_select_value_local(
            product_property=product_property,
            multiple=False,
            language_code=language_code,
        )
        return self._coerce_select_value_for_original_type(
            selected_value=selected_value,
            product_property=product_property,
            remote_property=remote_property,
        )

    def get_select_value_multiple(self, *, product_property=None, remote_property=None, language_code: Optional[str] = None):
        values = self.get_select_value_local(
            product_property=product_property,
            multiple=True,
            language_code=language_code,
        )
        return self._coerce_multiselect_for_textual_original(
            values=values,
            product_property=product_property,
            remote_property=remote_property,
        )

    def get_text_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        if value is None:
            return None

        translated_value = self.get_translated_values(
            product_property=product_property,
            language_code=language_code,
            fallback_value=value,
        )
        if translated_value in (None, ""):
            return translated_value

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        match (original_type, target_type):
            case (Property.TYPES.TEXT, Property.TYPES.TEXT):
                return self._coerce_text_value_for_textual_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case (Property.TYPES.INT, Property.TYPES.TEXT):
                try:
                    decimal_value = Decimal(str(translated_value).strip())
                except (InvalidOperation, TypeError, ValueError):
                    decimal_value = None

                if decimal_value is not None and decimal_value == decimal_value.to_integral_value():
                    return int(decimal_value)

                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a whole number",
                    provided_description="a decimal text value",
                    provided_value=translated_value,
                )

            case (Property.TYPES.FLOAT, Property.TYPES.TEXT):
                return self._coerce_float_textual_value(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                    provided_description="a non-numeric text value",
                )

            case (Property.TYPES.DESCRIPTION, Property.TYPES.TEXT):
                return self._coerce_text_value_for_textual_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case (Property.TYPES.BOOLEAN, Property.TYPES.TEXT):
                return self._coerce_boolean_text_for_boolean_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case ((Property.TYPES.SELECT | Property.TYPES.MULTISELECT), Property.TYPES.TEXT):
                return str(translated_value)

            case _:
                label = self._remote_property_label(
                    product_property=product_property,
                    remote_property=remote_property,
                )
                raise PreFlightCheckError(
                    f"Property '{label}' is mapped to a non-compatible type ({original_type} -> {target_type}) for text conversion."
                )

    def get_description_value(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        if value is None:
            return None

        translated_value = self.get_translated_values(
            product_property=product_property,
            language_code=language_code,
            fallback_value=value,
        )
        if translated_value in (None, ""):
            return translated_value

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        match (original_type, target_type):
            case (Property.TYPES.DESCRIPTION, Property.TYPES.DESCRIPTION):
                return self._coerce_text_value_for_textual_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case (Property.TYPES.INT, Property.TYPES.DESCRIPTION):
                try:
                    decimal_value = Decimal(str(translated_value).strip())
                except (InvalidOperation, TypeError, ValueError):
                    decimal_value = None

                if decimal_value is not None and decimal_value == decimal_value.to_integral_value():
                    return int(decimal_value)

                self._raise_value_expectation_preflight_error(
                    product_property=product_property,
                    remote_property=remote_property,
                    expected_description="a whole number",
                    provided_description="a decimal description value",
                    provided_value=translated_value,
                )

            case (Property.TYPES.FLOAT, Property.TYPES.DESCRIPTION):
                return self._coerce_float_textual_value(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                    provided_description="a non-numeric description value",
                )

            case (Property.TYPES.TEXT, Property.TYPES.DESCRIPTION):
                return self._ensure_text_length_for_text_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case (Property.TYPES.BOOLEAN, Property.TYPES.DESCRIPTION):
                return self._coerce_boolean_text_for_boolean_original(
                    translated_value=translated_value,
                    product_property=product_property,
                    remote_property=remote_property,
                )

            case ((Property.TYPES.SELECT | Property.TYPES.MULTISELECT), Property.TYPES.DESCRIPTION):
                return str(translated_value)

            case _:
                label = self._remote_property_label(
                    product_property=product_property,
                    remote_property=remote_property,
                )
                raise PreFlightCheckError(
                    f"Property '{label}' is mapped to a non-compatible type ({original_type} -> {target_type}) for description conversion."
                )

    def get_translated_values(self, *, product_property=None, language_code: Optional[str] = None, fallback_value=None):
        _ = product_property
        _ = language_code
        return fallback_value

    def format_date(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = language_code
        if not isinstance(value, (date, datetime)):
            return None

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        match (original_type, target_type):
            case (Property.TYPES.DATETIME, Property.TYPES.DATE):
                date_value = value.date() if isinstance(value, datetime) else value
                return datetime.combine(date_value, datetime.min.time()).isoformat()

            case _:
                return value.isoformat()[:10]

    def format_datetime(self, *, value, product_property=None, remote_property=None, language_code: Optional[str] = None):
        _ = language_code
        if not isinstance(value, (date, datetime)):
            return None

        original_type, target_type = self._resolve_original_and_target_types(
            product_property=product_property,
            remote_property=remote_property,
        )
        match (original_type, target_type):
            case (Property.TYPES.DATE, Property.TYPES.DATETIME):
                return value.isoformat()[:10]

            case _:
                if isinstance(value, datetime):
                    return value.isoformat()
                return datetime.combine(value, datetime.min.time()).isoformat()
