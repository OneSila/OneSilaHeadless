from __future__ import annotations

from typing import Any

from properties.models import ProductProperty, Property, PropertySelectValue


def describe_local_instance(*, local_instance: Any) -> str:
    if local_instance is None:
        return ""

    if isinstance(local_instance, Property):
        name = getattr(local_instance, "name", None)
        internal_name = getattr(local_instance, "internal_name", None)
        prop_type = getattr(local_instance, "type", None)
        parts = [part for part in (name, internal_name, prop_type) if part]
        if parts:
            return f" (Property: {' | '.join(parts)})"
        return " (Property)"

    if isinstance(local_instance, PropertySelectValue):
        prop = getattr(local_instance, "property", None)
        prop_name = getattr(prop, "name", None) if prop is not None else None
        value = None
        try:
            value = local_instance.value
        except Exception:  # pragma: no cover - defensive fallback
            value = None
        parts = [part for part in (prop_name, value) if part not in (None, "")]
        if parts:
            rendered = " | ".join(str(part) for part in parts)
            return f" (Property value: {rendered})"
        return " (Property value)"

    if isinstance(local_instance, ProductProperty):
        product = getattr(local_instance, "product", None)
        sku = getattr(product, "sku", None) if product is not None else None
        product_name = getattr(product, "name", None) if product is not None else None
        prop = getattr(local_instance, "property", None)
        prop_name = getattr(prop, "name", None) if prop is not None else None
        prop_type = getattr(prop, "type", None) if prop is not None else None
        value = None
        if prop_type == Property.TYPES.SELECT:
            selected = getattr(local_instance, "value_select", None)
            if selected is not None:
                try:
                    value = selected.value
                except Exception:  # pragma: no cover - defensive fallback
                    value = None
        elif prop_type == Property.TYPES.MULTISELECT:
            selected = getattr(local_instance, "value_multi_select", None)
            if selected is not None:
                try:
                    value = [item.value for item in selected.all()]
                except Exception:  # pragma: no cover - defensive fallback
                    value = None
        if value is None:
            try:
                value = local_instance.get_serialised_value()
            except Exception:  # pragma: no cover - defensive fallback
                value = None
        parts = [part for part in (sku, product_name, prop_name, value) if part not in (None, "", [], {})]
        if parts:
            rendered = " | ".join(str(part) for part in parts)
            return f" (Product property: {rendered})"
        return " (Product property)"

    return ""
