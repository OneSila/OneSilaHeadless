from __future__ import annotations

import json
from collections import defaultdict
from types import SimpleNamespace
from typing import Any

from core.models.multi_tenant import MultiTenantCompany
from imports_exports.factories.products import ImportProductInstance
from products.mcp.helpers import get_product_detail_queryset, serialize_product_detail
from products.mcp.types import (
    ProductBatchMutationPayload,
    ProductDetailPayload,
    ProductImageInputPayload,
    ProductMutationPayload,
    ProductPropertyTranslationInputPayload,
    ProductPropertyValueUpdateInputPayload,
)
from products.models import Product
from properties.mcp.helpers import get_company_language_codes
from properties.models import Property
from sales_channels.models import SalesChannel


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
        value_is_id = bool(update.get("value_is_id", False))

        if property_id is None and not property_internal_name:
            raise ValueError("Each property update must include property_id or property_internal_name.")
        if value is None:
            raise ValueError("Each property update must include value.")

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


def get_product_detail_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
) -> ProductDetailPayload:
    product_instance = get_product_detail_queryset(
        multi_tenant_company=multi_tenant_company,
    ).get(id=product.id)
    return serialize_product_detail(product=product_instance)


def build_product_mutation_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
) -> ProductMutationPayload:
    return {
        "updated": True,
        "product": get_product_detail_payload(
            multi_tenant_company=multi_tenant_company,
            product=product,
        ),
    }


def build_product_batch_mutation_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    updated_count: int,
) -> ProductBatchMutationPayload:
    return {
        "updated_count": updated_count,
        "product": get_product_detail_payload(
            multi_tenant_company=multi_tenant_company,
            product=product,
        ),
    }


def resolve_properties_for_updates(
    *,
    multi_tenant_company: MultiTenantCompany,
    updates: list[ProductPropertyValueUpdateInputPayload],
):
    resolved_updates = []
    for update in updates:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)
        if update.get("property_id") is not None:
            queryset = queryset.filter(id=update["property_id"])
        if update.get("property_internal_name"):
            queryset = queryset.filter(internal_name__iexact=update["property_internal_name"])

        property_ids = list(queryset.order_by("id").values_list("id", flat=True).distinct()[:2])
        if not property_ids:
            raise ValueError("Property not found for one of the provided updates.")
        if len(property_ids) > 1:
            raise ValueError("Multiple properties matched one of the provided updates.")

        property_instance = queryset.get(id=property_ids[0])
        resolved_update = {
            "property": property_instance,
            "value": update["value"],
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
