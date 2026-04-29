from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from core.models.multi_tenant import MultiTenantCompany
from django.db import transaction
from django.db.models import Prefetch, Q
from currencies.models import Currency
from imports_exports.factories.products import ImportProductInstance
from llm.models import McpToolRun
from products.mcp.catalog_helpers import get_vat_rate_match
from products.mcp.types import (
    ProductImageInputPayload,
    ProductPriceUpsertInputPayload,
    ProductPropertyTranslationInputPayload,
    ProductPropertyValueUpdateInputPayload,
    ProductTranslationUpsertInputPayload,
    ProductUpsertAppliedUpdatesPayload,
    ProductUpsertPayload,
    WorkflowStateUpdateInputPayload,
)
from products.models import Product, ProductTranslation
from properties.mcp.helpers import get_company_language_codes
from properties.models import Property
from sales_channels.helpers import build_content_payload
from sales_channels.models import SalesChannel, SalesChannelView, SalesChannelViewAssign
from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState

TRANSLATION_SEED_CONTENT_FLAGS = {"subtitle": True, "bulletPoints": True}


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


def resolve_vat_rate_update_data(
    *,
    multi_tenant_company: MultiTenantCompany,
    vat_rate_id: int | None,
    vat_rate: int | None,
) -> dict[str, Any]:
    vat_rate_instance = get_vat_rate_match(
        multi_tenant_company=multi_tenant_company,
        vat_rate_id=vat_rate_id,
        vat_rate=vat_rate,
    )
    if vat_rate_instance is None:
        return {}

    if vat_rate_instance.rate is not None:
        return {"vat_rate": vat_rate_instance.rate}

    return {
        "vat_rate": vat_rate_instance.name,
        "use_vat_rate_name": True,
    }


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
            "Use get_company_details with show_languages=true to see the allowed company languages."
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
                "Use get_company_details with show_languages=true to see the allowed company languages."
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
        image_content = str(image.get("image_content", "")).strip()
        if not image_url and not image_content:
            raise ValueError("Each image entry must include image_url or image_content.")

        sanitized_image: ProductImageInputPayload = {}
        if image_url:
            sanitized_image["image_url"] = image_url
        if image_content:
            sanitized_image["image_content"] = image_content
        for optional_key in ["title", "description", "type"]:
            if image.get(optional_key) not in (None, ""):
                sanitized_image[optional_key] = str(image[optional_key]).strip()
        for optional_key in ["is_main_image", "sort_order"]:
            if optional_key in image and image[optional_key] is not None:
                sanitized_image[optional_key] = image[optional_key]
        if "sales_channel_id" in image and image["sales_channel_id"] is not None:
            sanitized_image["sales_channel_id"] = int(image["sales_channel_id"])
        sanitized_images.append(sanitized_image)

    return sanitized_images


def sanitize_sales_channel_view_ids_input(
    *,
    sales_channel_view_ids: list[int] | str | None,
) -> list[int] | None:
    if sales_channel_view_ids is None:
        return None
    if isinstance(sales_channel_view_ids, str):
        try:
            sales_channel_view_ids = json.loads(sales_channel_view_ids)
        except json.JSONDecodeError as error:
            raise ValueError(
                "sales_channel_view_ids must be a list of ids, or a JSON string encoding that list."
            ) from error

    if not isinstance(sales_channel_view_ids, list) or not sales_channel_view_ids:
        raise ValueError("sales_channel_view_ids must be a non-empty list of ids.")

    sanitized_ids: list[int] = []
    seen_ids: set[int] = set()
    for raw_id in sales_channel_view_ids:
        try:
            view_id = int(raw_id)
        except (TypeError, ValueError) as error:
            raise ValueError("Each sales_channel_view_id must be an integer.") from error
        if view_id < 1:
            raise ValueError("Each sales_channel_view_id must be greater than or equal to 1.")
        if view_id in seen_ids:
            continue
        seen_ids.add(view_id)
        sanitized_ids.append(view_id)

    return sanitized_ids


def sanitize_workflows_input(
    *,
    workflows: list[WorkflowStateUpdateInputPayload] | str | None,
) -> list[WorkflowStateUpdateInputPayload] | None:
    if workflows is None:
        return None
    if isinstance(workflows, str):
        try:
            workflows = json.loads(workflows)
        except json.JSONDecodeError as error:
            raise ValueError(
                "workflows must be a list of objects with workflow_code and state_code, or a JSON string encoding that list."
            ) from error

    if not isinstance(workflows, list) or not workflows:
        raise ValueError("workflows must be a non-empty list.")

    sanitized_workflows: list[WorkflowStateUpdateInputPayload] = []
    seen_workflow_codes: set[str] = set()
    for workflow_update in workflows:
        if not isinstance(workflow_update, dict):
            raise ValueError("Each workflow update must be an object.")

        workflow_code = str(workflow_update.get("workflow_code", "")).strip().upper()
        state_code = str(workflow_update.get("state_code", "")).strip().upper()

        if not workflow_code:
            raise ValueError("Each workflow update must include workflow_code.")
        if not state_code:
            raise ValueError("Each workflow update must include state_code.")
        if workflow_code in seen_workflow_codes:
            raise ValueError("Duplicate workflow_code in workflows updates.")

        seen_workflow_codes.add(workflow_code)
        sanitized_workflows.append(
            {
                "workflow_code": workflow_code,
                "state_code": state_code,
            }
        )

    return sanitized_workflows


def sanitize_product_prices_input(
    *,
    prices: list[ProductPriceUpsertInputPayload] | str | None,
) -> list[ProductPriceUpsertInputPayload] | None:
    if prices is None:
        return None
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except json.JSONDecodeError as error:
            raise ValueError(
                "prices must be a list of price update objects, or a JSON string encoding that list."
            ) from error

    if not isinstance(prices, list) or not prices:
        raise ValueError("prices must be a non-empty list of price update objects.")

    sanitized_prices: list[ProductPriceUpsertInputPayload] = []
    seen_currencies: set[str] = set()
    for price_update in prices:
        if not isinstance(price_update, dict):
            raise ValueError("Each price update must be an object.")

        currency = str(price_update.get("currency", "")).strip().upper()
        if not currency:
            raise ValueError("Each price update must include currency.")
        if price_update.get("price") is None:
            raise ValueError("Each price update must include price.")
        if currency in seen_currencies:
            raise ValueError("Duplicate currency in price updates.")
        seen_currencies.add(currency)

        sanitized_price: ProductPriceUpsertInputPayload = {
            "currency": currency,
            "price": price_update["price"],
        }
        if "rrp" in price_update:
            sanitized_price["rrp"] = price_update.get("rrp")
        sanitized_prices.append(sanitized_price)

    return sanitized_prices


def sanitize_product_translation_updates_input(
    *,
    translations: list[ProductTranslationUpsertInputPayload] | str | None,
    multi_tenant_company: MultiTenantCompany,
) -> list[ProductTranslationUpsertInputPayload] | None:
    if translations is None:
        return None
    if isinstance(translations, str):
        try:
            translations = json.loads(translations)
        except json.JSONDecodeError as error:
            raise ValueError(
                "translations must be a list of translation update objects, or a JSON string encoding that list."
            ) from error

    if not isinstance(translations, list) or not translations:
        raise ValueError("translations must be a non-empty list of translation update objects.")

    sanitized_translations: list[ProductTranslationUpsertInputPayload] = []
    seen_translation_targets: set[tuple[str, int | None]] = set()
    for translation in translations:
        if not isinstance(translation, dict):
            raise ValueError("Each translation update must be an object.")

        language = validate_company_language(
            language=str(translation.get("language", "")),
            multi_tenant_company=multi_tenant_company,
        )
        sales_channel_id = translation.get("sales_channel_id")
        if sales_channel_id is not None:
            sales_channel_id = int(sales_channel_id)

        content_keys = [
            "name",
            "subtitle",
            "short_description",
            "description",
            "bullet_points",
        ]
        if not any(key in translation for key in content_keys):
            raise ValueError(
                "Each translation update must include at least one content field: "
                "name, subtitle, short_description, description, or bullet_points."
            )

        translation_key = (language, sales_channel_id)
        if translation_key in seen_translation_targets:
            raise ValueError("Duplicate translation target in updates.")
        seen_translation_targets.add(translation_key)

        sanitized_translation: ProductTranslationUpsertInputPayload = {
            "language": language,
        }
        if sales_channel_id is not None:
            sanitized_translation["sales_channel_id"] = sales_channel_id
        for field_name in ["name", "subtitle", "short_description", "description"]:
            if field_name in translation:
                sanitized_translation[field_name] = translation.get(field_name)
        if "bullet_points" in translation:
            sanitized_translation["bullet_points"] = sanitize_bullet_points_input(
                bullet_points=translation.get("bullet_points"),
            ) or []

        sanitized_translations.append(sanitized_translation)

    return sanitized_translations


def get_existing_translation_seed(
    *,
    product: Product,
    language: str,
    sales_channel,
) -> dict[str, Any]:
    content_payload = build_content_payload(
        product=product,
        sales_channel=sales_channel,
        language=language,
        flags_override=TRANSLATION_SEED_CONTENT_FLAGS,
    )
    if not content_payload:
        return {
            "name": product.name,
            "subtitle": None,
            "short_description": None,
            "description": None,
            "bullet_points": [],
        }

    return {
        "name": content_payload.get("name") or product.name,
        "subtitle": content_payload.get("subtitle"),
        "short_description": content_payload.get("shortDescription"),
        "description": content_payload.get("description"),
        "bullet_points": content_payload.get("bulletPoints", []),
    }


def get_translation_seed_product(*, product: Product) -> Product:
    return Product.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=ProductTranslation.objects.select_related("sales_channel")
            .prefetch_related("bullet_points")
            .order_by("language", "sales_channel_id", "id"),
        )
    ).get(id=product.id)


def resolve_sales_channels_map(
    *,
    multi_tenant_company: MultiTenantCompany,
    sales_channel_ids: set[int],
) -> dict[int, SalesChannel]:
    if not sales_channel_ids:
        return {}

    sales_channels = list(
        SalesChannel.objects.filter(
            multi_tenant_company=multi_tenant_company,
            id__in=sales_channel_ids,
        )
    )
    sales_channels_by_id = {
        sales_channel.id: sales_channel
        for sales_channel in sales_channels
    }
    missing_sales_channel_ids = sorted(sales_channel_ids - set(sales_channels_by_id))
    if missing_sales_channel_ids:
        raise ValueError("Sales channel not found.")

    return sales_channels_by_id


def resolve_price_updates(
    *,
    multi_tenant_company: MultiTenantCompany,
    prices: list[ProductPriceUpsertInputPayload],
) -> list[dict[str, Any]]:
    currencies_by_iso = {
        currency.iso_code: currency
        for currency in Currency.objects.select_related("inherits_from").filter(
            multi_tenant_company=multi_tenant_company,
            iso_code__in={price_update["currency"] for price_update in prices},
        )
    }

    resolved_prices: list[dict[str, Any]] = []
    for price_update in prices:
        iso_code = price_update["currency"]
        currency = currencies_by_iso.get(iso_code)
        if currency is None:
            raise ValueError(
                f"Currency {iso_code!r} is not configured for this account. "
                "Use get_company_details with show_currencies=true to confirm available currencies before editing prices."
            )
        if currency.inherits_from_id is not None:
            raise ValueError(
                f"Currency {iso_code!r} inherits its price from {currency.inherits_from.iso_code!r} "
                "and cannot be edited directly. Update the base currency price instead."
            )

        resolved_price = {
            "currency": currency.iso_code,
            "price": price_update["price"],
            "rrp": price_update.get("rrp"),
        }
        resolved_prices.append(resolved_price)

    return resolved_prices


def build_translation_update_groups(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    translations: list[ProductTranslationUpsertInputPayload],
) -> list[tuple[SalesChannel | None, list[dict[str, Any]]]]:
    sales_channel_ids = {
        int(translation["sales_channel_id"])
        for translation in translations
        if translation.get("sales_channel_id") is not None
    }
    sales_channels_by_id = resolve_sales_channels_map(
        multi_tenant_company=multi_tenant_company,
        sales_channel_ids=sales_channel_ids,
    )
    seed_product = get_translation_seed_product(product=product)
    grouped_translations: dict[int | None, list[dict[str, Any]]] = defaultdict(list)

    for translation in translations:
        sales_channel_id = translation.get("sales_channel_id")
        sales_channel = sales_channels_by_id.get(sales_channel_id) if sales_channel_id is not None else None
        seed_data = get_existing_translation_seed(
            product=seed_product,
            language=translation["language"],
            sales_channel=sales_channel,
        )
        translation_payload = {
            "language": translation["language"],
            "name": translation["name"] if "name" in translation else seed_data["name"],
        }
        for field_name in ["subtitle", "short_description", "description", "bullet_points"]:
            if field_name in translation:
                translation_payload[field_name] = translation[field_name]

        grouped_translations[sales_channel_id].append(translation_payload)

    return [
        (
            sales_channels_by_id.get(sales_channel_id),
            grouped_payloads,
        )
        for sales_channel_id, grouped_payloads in grouped_translations.items()
    ]


def run_product_import_update(
    *,
    import_process: McpToolRun,
    product: Product,
    product_data: dict[str, Any],
    sales_channel=None,
):
    import_instance = ImportProductInstance(
        product_data,
        import_process=import_process,
        instance=product,
        sales_channel=sales_channel,
    )
    import_instance.process()
    return import_instance


def build_product_confirmation_message(*, action: str) -> str:
    return "Updated successfully. Use get_product for details."


def build_product_upsert_payload(
    *,
    product: Product,
    applied_updates: ProductUpsertAppliedUpdatesPayload,
    action: str,
) -> ProductUpsertPayload:
    payload: ProductUpsertPayload = {
        "updated": True,
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "message": build_product_confirmation_message(action=action),
        "applied_updates": applied_updates,
    }
    if product.active is not None:
        payload["active"] = bool(product.active)
    return payload


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


def resolve_sales_channel_views_map(
    *,
    multi_tenant_company: MultiTenantCompany,
    sales_channel_view_ids: list[int],
) -> dict[int, SalesChannelView]:
    if not sales_channel_view_ids:
        return {}

    views = list(
        SalesChannelView.objects.select_related("sales_channel").filter(
            multi_tenant_company=multi_tenant_company,
            id__in=sales_channel_view_ids,
        )
    )
    views_by_id = {view.id: view for view in views}
    missing_view_ids = sorted(set(sales_channel_view_ids) - set(views_by_id))
    if missing_view_ids:
        raise ValueError(
            "Sales channel view not found. Use search_sales_channels to find valid website/storefront view ids."
        )

    return views_by_id


def assign_product_to_sales_channel_views(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    sales_channel_view_ids: list[int],
) -> int:
    views_by_id = resolve_sales_channel_views_map(
        multi_tenant_company=multi_tenant_company,
        sales_channel_view_ids=sales_channel_view_ids,
    )
    created_count = 0
    for view_id in sales_channel_view_ids:
        sales_channel_view = views_by_id[view_id]
        _, created = SalesChannelViewAssign.objects.get_or_create(
            multi_tenant_company=multi_tenant_company,
            product=product,
            sales_channel_view=sales_channel_view,
            defaults={
                "sales_channel": sales_channel_view.sales_channel,
            },
        )
        if created:
            created_count += 1

    return created_count


def resolve_workflow_updates(
    *,
    multi_tenant_company: MultiTenantCompany,
    workflows: list[WorkflowStateUpdateInputPayload],
) -> list[tuple[Workflow, WorkflowState]]:
    workflow_codes = {
        workflow_update["workflow_code"]
        for workflow_update in workflows
    }
    state_codes = {
        workflow_update["state_code"]
        for workflow_update in workflows
    }
    workflows_by_code = {
        workflow.code: workflow
        for workflow in Workflow.objects.filter(
            multi_tenant_company=multi_tenant_company,
            code__in=workflow_codes,
        )
    }
    missing_workflow_codes = sorted(workflow_codes - set(workflows_by_code))
    if missing_workflow_codes:
        raise ValueError(
            "Workflow not found for one of the provided workflow_code values. "
            "Use get_company_details with show_workflows=true to get valid workflow codes."
        )

    states = list(
        WorkflowState.objects.select_related("workflow").filter(
            workflow__multi_tenant_company=multi_tenant_company,
            code__in=state_codes,
        )
    )
    states_by_workflow_and_code = {
        (state.workflow_id, state.code): state
        for state in states
    }

    resolved_updates: list[tuple[Workflow, WorkflowState]] = []
    for workflow_update in workflows:
        workflow = workflows_by_code[workflow_update["workflow_code"]]
        state = states_by_workflow_and_code.get((workflow.id, workflow_update["state_code"]))
        if state is None:
            raise ValueError(
                f"State code {workflow_update['state_code']!r} does not belong to workflow {workflow.code!r}. "
                "Use get_company_details with show_workflows=true to get valid workflow/state code pairs."
            )
        resolved_updates.append((workflow, state))

    return resolved_updates


def apply_workflow_updates(
    *,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    workflows: list[WorkflowStateUpdateInputPayload],
) -> int:
    resolved_updates = resolve_workflow_updates(
        multi_tenant_company=multi_tenant_company,
        workflows=workflows,
    )
    changed_count = 0
    for workflow, state in resolved_updates:
        assignment, created = WorkflowProductAssignment.objects.get_or_create(
            multi_tenant_company=multi_tenant_company,
            workflow=workflow,
            product=product,
            defaults={"workflow_state": state},
        )
        if created:
            changed_count += 1
            continue

        if assignment.workflow_state_id != state.id:
            assignment.workflow_state = state
            assignment.save(update_fields=["workflow_state"])
            changed_count += 1

    return changed_count


def run_upsert_product_updates(
    *,
    import_process: McpToolRun,
    multi_tenant_company: MultiTenantCompany,
    product: Product,
    vat_rate_id: int | None,
    vat_rate: int | None,
    active: bool | None,
    ean_code: str | None,
    translations: list[ProductTranslationUpsertInputPayload] | None,
    prices: list[ProductPriceUpsertInputPayload] | None,
    properties: list[ProductPropertyValueUpdateInputPayload] | None,
    images: list[ProductImageInputPayload] | None,
    sales_channel_view_ids: list[int] | None,
    workflows: list[WorkflowStateUpdateInputPayload] | None,
) -> ProductUpsertPayload:
    applied_updates: ProductUpsertAppliedUpdatesPayload = {}

    with transaction.atomic():
        core_product_data: dict[str, Any] = {}
        if vat_rate_id is not None or vat_rate is not None:
            core_product_data.update(
                resolve_vat_rate_update_data(
                    multi_tenant_company=multi_tenant_company,
                    vat_rate_id=vat_rate_id,
                    vat_rate=vat_rate,
                )
            )
            applied_updates["vat_rate"] = True
        if active is not None:
            core_product_data["active"] = active
            applied_updates["active"] = bool(active)
        if ean_code is not None:
            core_product_data["ean_code"] = ean_code
            applied_updates["ean_code"] = True
        if prices:
            core_product_data["prices"] = resolve_price_updates(
                multi_tenant_company=multi_tenant_company,
                prices=prices,
            )
            applied_updates["prices"] = len(prices)
        if properties:
            core_product_data["properties"] = resolve_properties_for_updates(
                multi_tenant_company=multi_tenant_company,
                updates=properties,
            )
            applied_updates["properties"] = len(properties)
        if core_product_data:
            run_product_import_update(
                import_process=import_process,
                product=product,
                product_data=core_product_data,
            )

        if translations:
            translation_groups = build_translation_update_groups(
                multi_tenant_company=multi_tenant_company,
                product=product,
                translations=translations,
            )
            for sales_channel, grouped_payload in translation_groups:
                run_product_import_update(
                    import_process=import_process,
                    product=product,
                    product_data={"translations": grouped_payload},
                    sales_channel=sales_channel,
                )
            applied_updates["translations"] = len(translations)

        if images:
            sales_channels_by_id = resolve_sales_channels_map(
                multi_tenant_company=multi_tenant_company,
                sales_channel_ids={
                    int(image["sales_channel_id"])
                    for image in images
                    if image.get("sales_channel_id") is not None
                },
            )
            updated_images_count = 0
            grouped_images = group_images_by_sales_channel_id(images=images)
            for sales_channel_id, grouped_payload in grouped_images.items():
                import_instance = run_product_import_update(
                    import_process=import_process,
                    product=product,
                    product_data={"images": grouped_payload},
                    sales_channel=sales_channels_by_id.get(sales_channel_id),
                )
                updated_images_count += import_instance.images_associations_instances.count()
            applied_updates["images"] = updated_images_count

        if sales_channel_view_ids:
            applied_updates["website_views_assignments"] = assign_product_to_sales_channel_views(
                multi_tenant_company=multi_tenant_company,
                product=product,
                sales_channel_view_ids=sales_channel_view_ids,
            )
        if workflows:
            applied_updates["workflows"] = apply_workflow_updates(
                multi_tenant_company=multi_tenant_company,
                product=product,
                workflows=workflows,
            )

    product.refresh_from_db()
    return build_product_upsert_payload(
        product=product,
        applied_updates=applied_updates,
        action="product upsert",
    )
