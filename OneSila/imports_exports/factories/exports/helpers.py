from typing import Iterable

from integrations.helpers import resolve_public_integration_lookup
from products.models import ProductTranslation
from properties.models import (
    ProductProperty,
    ProductPropertyTextTranslation,
    Property,
    PropertySelectValue,
)

def build_product_stub(*, product):
    return {
        "sku": product.sku,
        "type": product.type,
    }


def serialize_property_translations(*, property_instance, language=None):
    return [
        {
            "language": translation.language,
            "name": translation.name,
        }
        for translation in property_instance.propertytranslation_set.all().order_by("language")
        if language in (None, translation.language)
    ]


def serialize_property_data(
    *,
    property_instance,
    include_translations=True,
    language=None,
):
    data = {
        "name": property_instance.name,
        "internal_name": property_instance.internal_name,
        "type": property_instance.type,
        "is_public_information": property_instance.is_public_information,
        "add_to_filters": property_instance.add_to_filters,
        "has_image": property_instance.has_image,
        "is_product_type": property_instance.is_product_type,
    }
    if include_translations:
        data["translations"] = serialize_property_translations(
            property_instance=property_instance,
            language=language,
        )
    return data


def serialize_select_value_translations(*, select_value, language=None):
    return [
        {
            "language": translation.language,
            "value": translation.value,
        }
        for translation in select_value.propertyselectvaluetranslation_set.all().order_by("language")
        if language in (None, translation.language)
    ]


def serialize_property_select_value_data(
    *,
    select_value,
    language=None,
    values_are_ids=False,
    include_translations=False,
    include_property_data=False,
    include_id=False,
):
    value = select_value.id if values_are_ids else select_value.value_by_language_code(language=language)
    data = {
        "value": value,
    }

    if include_id:
        data["id"] = select_value.id

    if include_property_data:
        data["property_data"] = serialize_property_data(
            property_instance=select_value.property,
            include_translations=include_translations,
            language=language,
        )

    if include_translations:
        data["translations"] = serialize_select_value_translations(
            select_value=select_value,
            language=language,
        )

    return data


def serialize_product_translation_payload(*, translation):
    payload = {
        "language": translation.language,
        "name": translation.name,
        "sales_channel": serialize_translation_sales_channel(
            sales_channel=translation.sales_channel,
        ),
    }

    if translation.subtitle:
        payload["subtitle"] = translation.subtitle
    if translation.short_description:
        payload["short_description"] = translation.short_description
    if translation.description:
        payload["description"] = translation.description
    if translation.url_key:
        payload["url_key"] = translation.url_key

    bullet_points = list(
        translation.bullet_points.all().order_by("sort_order").values_list("text", flat=True)
    )
    if bullet_points:
        payload["bullet_points"] = bullet_points

    return payload


def serialize_translation_sales_channel(*, sales_channel):
    return sales_channel.id if sales_channel is not None else None


def serialize_sales_channel_payload(*, sales_channel):
    integration_type, subtype = resolve_public_integration_lookup(
        integration=sales_channel,
    )
    return {
        "id": sales_channel.id,
        "hostname": sales_channel.hostname,
        "type": integration_type,
        "subtype": subtype,
    }


def get_product_translation_payloads(
    *,
    product,
    language=None,
    sales_channel=None,
):
    selected = list(product.translations.all())
    if language is not None:
        selected = [
            translation
            for translation in selected
            if translation.language == language
        ]

    if language is not None and sales_channel is not None:
        selected_for_channel = [
            translation
            for translation in selected
            if translation.sales_channel_id == sales_channel.id
        ]
        if selected_for_channel:
            selected = selected_for_channel
        else:
            selected = [
                translation
                for translation in selected
                if translation.sales_channel_id is None
            ]

    selected.sort(
        key=lambda translation: (
            translation.language,
            translation.sales_channel_id is not None,
            (translation.sales_channel.hostname if translation.sales_channel_id else ""),
        )
    )
    return [
        serialize_product_translation_payload(translation=translation)
        for translation in selected
    ]


def get_product_property_text_translation_map(*, product_property):
    return {
        translation.language: translation
        for translation in product_property.productpropertytexttranslation_set.all()
    }


def serialize_product_property_value(
    *,
    product_property,
    language=None,
    values_are_ids=False,
    include_translations=False,
    include_value_ids=False,
):
    property_type = product_property.property.type

    if property_type == Property.TYPES.INT:
        primitive_value = product_property.value_int
        return primitive_value, [{"value": primitive_value}]

    if property_type == Property.TYPES.FLOAT:
        primitive_value = product_property.value_float
        return primitive_value, [{"value": primitive_value}]

    if property_type == Property.TYPES.BOOLEAN:
        primitive_value = product_property.value_boolean
        return primitive_value, [{"value": primitive_value}]

    if property_type == Property.TYPES.DATE:
        primitive_value = (
            product_property.value_date.isoformat()
            if product_property.value_date is not None
            else None
        )
        return primitive_value, [{"value": primitive_value}]

    if property_type == Property.TYPES.DATETIME:
        primitive_value = (
            product_property.value_datetime.isoformat()
            if product_property.value_datetime is not None
            else None
        )
        return primitive_value, [{"value": primitive_value}]

    if property_type in (Property.TYPES.TEXT, Property.TYPES.DESCRIPTION):
        translation_map = get_product_property_text_translation_map(
            product_property=product_property,
        )
        active_translation = translation_map.get(language) if language else None
        if active_translation is None and translation_map:
            active_translation = next(iter(translation_map.values()))

        field_name = "value_text" if property_type == Property.TYPES.TEXT else "value_description"
        primitive_value = getattr(active_translation, field_name, None) if active_translation else None
        values = [{"value": primitive_value}]

        if include_translations:
            values[0]["translations"] = [
                {
                    "language": item.language,
                    "value": getattr(item, field_name, None),
                }
                for item in translation_map.values()
                if language in (None, item.language)
                if getattr(item, field_name, None) not in (None, "")
            ]

        return primitive_value, values

    if property_type == Property.TYPES.SELECT:
        select_value = product_property.value_select
        if select_value is None:
            return None, []

        primitive_value = (
            select_value.id
            if values_are_ids
            else select_value.value_by_language_code(language=language)
        )
        value_data = serialize_property_select_value_data(
            select_value=select_value,
            language=language,
            values_are_ids=values_are_ids,
            include_translations=include_translations,
            include_id=include_value_ids,
        )
        return primitive_value, [value_data]

    if property_type == Property.TYPES.MULTISELECT:
        select_values = list(product_property.value_multi_select.all())
        primitive_value = [
            select_value.id if values_are_ids else select_value.value_by_language_code(language=language)
            for select_value in select_values
        ]
        values = [
            serialize_property_select_value_data(
                select_value=select_value,
                language=language,
                values_are_ids=values_are_ids,
                include_translations=include_translations,
                include_id=include_value_ids,
            )
            for select_value in select_values
        ]
        return primitive_value, values

    return None, []


def build_requirement_map(*, rule):
    if rule is None:
        return {}
    return {
        item.property_id: item.type
        for item in rule.items.all()
    }


def filter_queryset_by_ids(*, queryset, field_name="id", ids=None):
    if not ids:
        return queryset
    return queryset.filter(**{f"{field_name}__in": ids})


def to_bool(*, value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def unique_by_id(*, items: Iterable):
    seen_ids = set()
    unique_items = []
    for item in items:
        if item.id in seen_ids:
            continue
        seen_ids.add(item.id)
        unique_items.append(item)
    return unique_items
