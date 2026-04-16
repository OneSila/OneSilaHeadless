from __future__ import annotations

import json
from collections import defaultdict
from types import SimpleNamespace
from typing import Any

from core.models.multi_tenant import MultiTenantCompany
from django.db.models import Q
from currencies.models import Currency
from imports_exports.factories.products import ImportProductInstance
from products.mcp.types import (
    ProductBatchMutationPayload,
    ProductImageInputPayload,
    ProductMutationPayload,
    ProductPropertyTranslationInputPayload,
    ProductPropertyValueUpdateInputPayload,
)
from products.models import Product
from properties.mcp.helpers import get_company_language_codes
from properties.models import Property
from sales_channels.models import SalesChannel


def parse_boolean_input(*, value, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized_value = value.strip().lower()
        if normalized_value in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized_value in {"0", "false", "no", "n", "off"}:
            return False

    raise ValueError(
        f"{field_name} must be a boolean or a boolean-like string such as true/false, got: {value!r}"
    )


def split_comma_separated_values(*, value: str) -> list[str]:
    return [chunk.strip() for chunk in value.split(",") if chunk.strip()]


def normalize_property_update_value(
    *,
    property_instance: Property,
    value,
    value_is_id: bool,
):
    if property_instance.type == Property.TYPES.BOOLEAN:
        return parse_boolean_input(
            value=value,
            field_name=f"value for property {property_instance.internal_name or property_instance.id}",
        )

    if property_instance.type == Property.TYPES.SELECT and value_is_id:
        return int(value)

    if property_instance.type == Property.TYPES.MULTISELECT and value_is_id:
        raw_values = value
        if isinstance(raw_values, str):
            raw_values = split_comma_separated_values(value=raw_values)
        elif isinstance(raw_values, (list, tuple, set)):
            raw_values = list(raw_values)
        else:
            raw_values = [raw_values]

        try:
            return [int(item) for item in raw_values]
        except (TypeError, ValueError) as error:
            raise ValueError(
                "MULTISELECT values with value_is_id=true must be a list of ids or a comma-separated string of ids."
            ) from error

    return value


def build_product_import_process(*, multi_tenant_company: MultiTenantCompany):
    return SimpleNamespace(
        multi_tenant_company=multi_tenant_company,
        create_only=False,
        update_only=False,
        override_only=False,
    )


def get_product_match(
    *,
    multi_tenant_company: MultiTenantCompany,
    product_id: int | None,
    sku: str | None,
):
    queryset = Product.objects.filter(multi_tenant_company=multi_tenant_company)

    if not any([product_id is not None, sku]):
        raise ValueError("Provide product_id or sku.")

    if product_id is not None:
        queryset = queryset.filter(id=product_id)
    if sku:
        queryset = queryset.filter(sku=sku)

    product_ids = list(queryset.order_by("id").values_list("id", flat=True).distinct()[:2])

    if not product_ids:
        raise ValueError("Product not found.")
    if len(product_ids) > 1:
        raise ValueError("Multiple products matched the provided identifiers.")

    return queryset.get(id=product_ids[0])


def get_sales_channel_match(
    *,
    multi_tenant_company: MultiTenantCompany,
    sales_channel_id: int | None,
):
    if sales_channel_id is None:
        return None

    try:
        return SalesChannel.objects.get(
            id=sales_channel_id,
            multi_tenant_company=multi_tenant_company,
        )
    except SalesChannel.DoesNotExist as error:
        raise ValueError("Sales channel not found.") from error


def validate_company_language(
    *,
    language: str,
    multi_tenant_company: MultiTenantCompany,
) -> str:
    normalized_language = str(language or "").strip().lower()
    if not normalized_language:
        raise ValueError("language is required.")

    allowed_languages = set(get_company_language_codes(multi_tenant_company=multi_tenant_company))
    if normalized_language not in allowed_languages:
        raise ValueError(
            f"Unsupported language: {normalized_language!r}. "
            "Use get_company_languages to see the allowed company languages."
        )

    return normalized_language


def get_company_currency_match(
    *,
    multi_tenant_company: MultiTenantCompany,
    iso_code: str,
) -> Currency:
    normalized_iso_code = str(iso_code or "").strip().upper()
    if not normalized_iso_code:
        raise ValueError("currency is required.")

    try:
        currency = Currency.objects.select_related("inherits_from").get(
            multi_tenant_company=multi_tenant_company,
            iso_code=normalized_iso_code,
        )
    except Currency.DoesNotExist as error:
        raise ValueError(
            f"Currency {normalized_iso_code!r} is not configured for this account. "
            "Use get_vat_rates or account currency settings to confirm available configuration before editing prices."
        ) from error

    if currency.inherits_from_id is not None:
        raise ValueError(
            f"Currency {normalized_iso_code!r} inherits its price from {currency.inherits_from.iso_code!r} "
            "and cannot be edited directly. Update the base currency price instead."
        )

    return currency


def sanitize_bullet_points_input(
    *,
    bullet_points: list[str] | str | None,
) -> list[str] | None:
    if bullet_points is None:
        return None
    if isinstance(bullet_points, str):
        try:
            bullet_points = json.loads(bullet_points)
        except json.JSONDecodeError as error:
            raise ValueError(
                "bullet_points must be a list of strings, or a JSON string encoding that list."
            ) from error

    if not isinstance(bullet_points, list):
        raise ValueError("bullet_points must be a list of strings.")

    sanitized_points: list[str] = []
    for bullet_point in bullet_points:
        if not isinstance(bullet_point, str):
            raise ValueError("Each bullet point must be a string.")
        sanitized_points.append(bullet_point.strip())

    return sanitized_points


def sanitize_product_property_translations_input(
    *,
    translations: list[ProductPropertyTranslationInputPayload] | str | None,
    multi_tenant_company: MultiTenantCompany,
) -> list[ProductPropertyTranslationInputPayload] | None:
    if translations is None:
        return None
    if isinstance(translations, str):
        try:
            translations = json.loads(translations)
        except json.JSONDecodeError as error:
            raise ValueError(
                "translations must be a list of objects with language and value, or a JSON string encoding that list."
            ) from error

    if not isinstance(translations, list):
        raise ValueError("translations must be a list of objects with language and value.")

    allowed_languages = set(get_company_language_codes(multi_tenant_company=multi_tenant_company))
    sanitized_translations: list[ProductPropertyTranslationInputPayload] = []
    for translation in translations:
        if not isinstance(translation, dict):
            raise ValueError("Each translation must be an object with language and value.")

        language = str(translation.get("language", "")).strip().lower()
        value = translation.get("value")
        if not language:
            raise ValueError("Each translation must include a non-empty language.")
        if language not in allowed_languages:
            raise ValueError(
                f"Unsupported translation language: {language!r}. "
                "Use get_company_languages to see the allowed company languages."
            )
        if value in (None, ""):
            raise ValueError("Each translation must include a non-empty value.")

        sanitized_translations.append(
            {
                "language": language,
                "value": str(value),
            }
        )

    return sanitized_translations


def sanitize_product_property_updates_input(
    *,
    updates: list[ProductPropertyValueUpdateInputPayload] | str,
    multi_tenant_company: MultiTenantCompany,
) -> list[ProductPropertyValueUpdateInputPayload]:
    if isinstance(updates, str):
        try:
            updates = json.loads(updates)
        except json.JSONDecodeError as error:
            raise ValueError(
                "updates must be a list of property update objects, or a JSON string encoding that list."
            ) from error

    if not isinstance(updates, list) or not updates:
        raise ValueError("updates must be a non-empty list of property update objects.")

    sanitized_updates: list[ProductPropertyValueUpdateInputPayload] = []
    for update in updates:
        if not isinstance(update, dict):
            raise ValueError("Each property update must be an object.")

        property_id = update.get("property_id")
        property_internal_name = str(update.get("property_internal_name", "")).strip() or None
        value = update.get("value")
        raw_value_is_id = update.get("value_is_id", False)

        if property_id is None and not property_internal_name:
            raise ValueError("Each property update must include property_id or property_internal_name.")
        if value is None:
            raise ValueError("Each property update must include value.")

        value_is_id = parse_boolean_input(
            value=raw_value_is_id,
            field_name="value_is_id",
        ) if raw_value_is_id is not None else False

        translations = sanitize_product_property_translations_input(
            translations=update.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )

        sanitized_update: ProductPropertyValueUpdateInputPayload = {
            "value": value,
            "value_is_id": value_is_id,
        }
        if property_id is not None:
            sanitized_update["property_id"] = int(property_id)
        if property_internal_name:
            sanitized_update["property_internal_name"] = property_internal_name
        if translations is not None:
            sanitized_update["translations"] = translations
        sanitized_updates.append(sanitized_update)

    return sanitized_updates


def sanitize_product_images_input(
    *,
    images: list[ProductImageInputPayload] | str,
) -> list[ProductImageInputPayload]:
    if isinstance(images, str):
        try:
            images = json.loads(images)
        except json.JSONDecodeError as error:
            raise ValueError(
                "images must be a list of image objects, or a JSON string encoding that list."
            ) from error

    if not isinstance(images, list) or not images:
        raise ValueError("images must be a non-empty list of image objects.")

    sanitized_images: list[ProductImageInputPayload] = []
    for image in images:
        if not isinstance(image, dict):
            raise ValueError("Each image entry must be an object.")

        image_url = str(image.get("image_url", "")).strip()
        if not image_url:
            raise ValueError("Each image entry must include image_url.")

        sanitized_image: ProductImageInputPayload = {
            "image_url": image_url,
        }
        for optional_key in ["title", "description", "type"]:
            if image.get(optional_key) not in (None, ""):
                sanitized_image[optional_key] = str(image[optional_key]).strip()
        for optional_key in ["is_main_image", "sort_order", "sales_channel_id"]:
            if optional_key in image and image[optional_key] is not None:
                sanitized_image[optional_key] = image[optional_key]
        sanitized_images.append(sanitized_image)

    return sanitized_images


def get_existing_translation_seed(
    *,
    product: Product,
    language: str,
    sales_channel,
) -> dict[str, Any]:
    target_sales_channel_id = getattr(sales_channel, "id", None)
    translations = list(product.translations.all())

    current_translation = next(
        (
            translation for translation in translations
            if translation.language == language and translation.sales_channel_id == target_sales_channel_id
        ),
        None,
    )
    if current_translation is None and sales_channel is not None:
        current_translation = next(
            (
                translation for translation in translations
                if translation.language == language and translation.sales_channel_id is None
            ),
            None,
        )
    if current_translation is None:
        current_translation = next(
            (
                translation for translation in translations
                if translation.language == language
            ),
            None,
        )
    if current_translation is None and translations:
        current_translation = translations[0]

    if current_translation is None:
        return {
            "name": product.name,
            "subtitle": None,
            "short_description": None,
            "description": None,
            "bullet_points": [],
        }

    return {
        "name": current_translation.name or product.name,
        "subtitle": current_translation.subtitle,
        "short_description": current_translation.short_description,
        "description": current_translation.description,
        "bullet_points": [
            bullet_point.text
            for bullet_point in current_translation.bullet_points.order_by("sort_order", "id")
        ],
    }


def run_product_import_update(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    product_data: dict[str, Any],
    sales_channel=None,
):
    import_instance = ImportProductInstance(
        product_data,
        import_process=build_product_import_process(multi_tenant_company=multi_tenant_company),
        instance=product,
        sales_channel=sales_channel,
    )
    import_instance.process()
    return import_instance


def build_product_confirmation_message(*, action: str) -> str:
    return "Updated successfully. Use get_product for details."


def build_product_mutation_payload(
    *,
    product: Product,
    action: str,
) -> ProductMutationPayload:
    payload: ProductMutationPayload = {
        "updated": True,
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "message": build_product_confirmation_message(action=action),
    }
    if product.active is not None:
        payload["active"] = bool(product.active)
    return payload


def build_product_batch_mutation_payload(
    *,
    product: Product,
    updated_count: int,
    action: str,
) -> ProductBatchMutationPayload:
    return {
        "updated_count": updated_count,
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "message": "Processed successfully. Use get_product for details.",
    }


def resolve_properties_for_updates(
    *,
    multi_tenant_company: MultiTenantCompany,
    updates: list[ProductPropertyValueUpdateInputPayload],
):
    property_ids = {
        int(update["property_id"])
        for update in updates
        if update.get("property_id") is not None
    }
    property_internal_names = {
        str(update["property_internal_name"]).strip().lower()
        for update in updates
        if update.get("property_internal_name")
    }
    property_filters = Q()
    if property_ids:
        property_filters |= Q(id__in=property_ids)
    for property_internal_name in property_internal_names:
        property_filters |= Q(internal_name__iexact=property_internal_name)

    properties = list(
        Property.objects.filter(multi_tenant_company=multi_tenant_company).filter(property_filters)
    )
    properties_by_id = {
        property_instance.id: property_instance
        for property_instance in properties
    }
    properties_by_internal_name = {
        str(property_instance.internal_name).strip().lower(): property_instance
        for property_instance in properties
        if property_instance.internal_name
    }

    missing_ids = sorted(property_ids - set(properties_by_id))
    if missing_ids:
        raise ValueError("Property not found for one of the provided updates.")

    missing_internal_names = sorted(
        property_internal_names - set(properties_by_internal_name)
    )
    if missing_internal_names:
        raise ValueError("Property not found for one of the provided updates.")

    resolved_updates = []
    for update in updates:
        property_instance = None
        if update.get("property_id") is not None:
            property_instance = properties_by_id.get(int(update["property_id"]))
        if property_instance is None and update.get("property_internal_name"):
            property_instance = properties_by_internal_name.get(
                str(update["property_internal_name"]).strip().lower()
            )
        if property_instance is None:
            raise ValueError("Property not found for one of the provided updates.")

        resolved_update = {
            "property": property_instance,
            "value": normalize_property_update_value(
                property_instance=property_instance,
                value=update["value"],
                value_is_id=update.get("value_is_id", False),
            ),
            "value_is_id": update.get("value_is_id", False),
        }
        if update.get("translations") is not None:
            resolved_update["translations"] = update["translations"]
        resolved_updates.append(resolved_update)

    return resolved_updates


def group_images_by_sales_channel_id(
    *,
    images: list[ProductImageInputPayload],
):
    grouped_images: dict[int | None, list[dict[str, Any]]] = defaultdict(list)
    for image in images:
        grouped_images[image.get("sales_channel_id")].append(
            {
                key: value
                for key, value in image.items()
                if key != "sales_channel_id"
            }
        )
    return grouped_images
