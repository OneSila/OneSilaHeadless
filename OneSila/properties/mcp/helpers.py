from __future__ import annotations

import json
from types import SimpleNamespace

from core.models.multi_tenant import MultiTenantCompany
from django.db.models import Prefetch, QuerySet
from django.utils.translation import get_language_info

from properties.mcp.types import (
    CompanyLanguagePayload,
    CompanyLanguagesPayload,
    CreatePropertyPayload,
    CreatePropertySelectValuePayload,
    EditPropertyPayload,
    EditPropertySelectValuePayload,
    PropertyDetailPayload,
    PropertyReferencePayload,
    PropertySearchResultPayload,
    PropertySelectValueDetailPayload,
    PropertySelectValueSearchResultPayload,
    PropertySelectValueSummaryPayload,
    PropertySelectValueTranslationInputPayload,
    PropertyTranslationInputPayload,
)
from properties.models import Property, PropertySelectValue


PROPERTY_TYPE_LABELS = {
    code: str(label)
    for code, label in Property.TYPES.ALL
}


def get_property_type_label(*, type_value: str) -> str:
    return PROPERTY_TYPE_LABELS[type_value]


def build_import_process(*, multi_tenant_company: MultiTenantCompany):
    return SimpleNamespace(
        multi_tenant_company=multi_tenant_company,
        create_only=False,
        update_only=False,
        override_only=False,
    )


def get_company_language_codes(*, multi_tenant_company: MultiTenantCompany) -> list[str]:
    codes = [str(code).lower() for code in (multi_tenant_company.languages or []) if code]
    default_language = str(multi_tenant_company.language).lower()
    if default_language not in codes:
        codes.insert(0, default_language)
    return list(dict.fromkeys(codes))


def serialize_company_languages(*, multi_tenant_company: MultiTenantCompany) -> CompanyLanguagesPayload:
    default_language_code = str(multi_tenant_company.language).lower()
    enabled_languages: list[CompanyLanguagePayload] = []

    for code in get_company_language_codes(multi_tenant_company=multi_tenant_company):
        language_info = get_language_info(code)
        enabled_languages.append(
            {
                "code": code,
                "name": str(language_info["name"]),
                "name_local": str(language_info["name_local"]),
                "name_translated": str(language_info["name_translated"]),
                "bidi": language_info["bidi"],
                "is_default": code == default_language_code,
            }
        )

    return {
        "default_language_code": default_language_code,
        "enabled_languages": enabled_languages,
    }


def sanitize_property_translations_input(
    *,
    translations: list[PropertyTranslationInputPayload] | str | None,
) -> list[PropertyTranslationInputPayload] | None:
    if translations is None:
        return None
    if isinstance(translations, str):
        try:
            translations = json.loads(translations)
        except json.JSONDecodeError as error:
            raise ValueError(
                "translations must be a list of objects with language and name, or a JSON string encoding that list."
            ) from error
    if not isinstance(translations, list):
        raise ValueError("translations must be a list of objects with language and name.")

    sanitized_translations: list[PropertyTranslationInputPayload] = []
    for translation in translations:
        if not isinstance(translation, dict):
            raise ValueError("Each translation must be an object with language and name.")

        language = str(translation.get("language", "")).strip().lower()
        translated_name = str(translation.get("name", "")).strip()
        if not language or not translated_name:
            raise ValueError("Each translation must include non-empty language and name.")

        sanitized_translations.append(
            {
                "language": language,
                "name": translated_name,
            }
        )

    return sanitized_translations


def validate_translation_languages(
    *,
    translations: list[PropertyTranslationInputPayload] | None,
    multi_tenant_company: MultiTenantCompany,
) -> None:
    if not translations:
        return

    allowed_languages = set(get_company_language_codes(multi_tenant_company=multi_tenant_company))
    invalid_languages = sorted(
        {
            translation["language"]
            for translation in translations
            if translation["language"] not in allowed_languages
        }
    )

    if invalid_languages:
        raise ValueError(
            "Unsupported translation languages: "
            f"{invalid_languages}. Use get_company_details with show_languages=true to see the allowed company languages."
        )


def sanitize_select_value_translations_input(
    *,
    translations: list[PropertySelectValueTranslationInputPayload] | str | None,
) -> list[PropertySelectValueTranslationInputPayload] | None:
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

    sanitized_translations: list[PropertySelectValueTranslationInputPayload] = []
    for translation in translations:
        if not isinstance(translation, dict):
            raise ValueError("Each translation must be an object with language and value.")

        language = str(translation.get("language", "")).strip().lower()
        translated_value = str(translation.get("value", "")).strip()
        if not language or not translated_value:
            raise ValueError("Each translation must include non-empty language and value.")

        sanitized_translations.append(
            {
                "language": language,
                "value": translated_value,
            }
        )

    return sanitized_translations


def validate_select_value_translation_languages(
    *,
    translations: list[PropertySelectValueTranslationInputPayload] | None,
    multi_tenant_company: MultiTenantCompany,
) -> None:
    if not translations:
        return

    allowed_languages = set(get_company_language_codes(multi_tenant_company=multi_tenant_company))
    invalid_languages = sorted(
        {
            translation["language"]
            for translation in translations
            if translation["language"] not in allowed_languages
        }
    )

    if invalid_languages:
        raise ValueError(
            "Unsupported translation languages: "
            f"{invalid_languages}. Use get_company_details with show_languages=true to see the allowed company languages."
        )


def get_property_detail_queryset(*, multi_tenant_company: MultiTenantCompany) -> QuerySet[Property]:
    property_value_queryset = PropertySelectValue.objects.filter(
        multi_tenant_company=multi_tenant_company,
    ).prefetch_related("propertyselectvaluetranslation_set")

    return Property.objects.filter(multi_tenant_company=multi_tenant_company).prefetch_related(
        "propertytranslation_set",
        Prefetch("propertyselectvalue_set", queryset=property_value_queryset.order_by("id")),
    )


def get_property_select_value_detail_queryset(*, multi_tenant_company: MultiTenantCompany):
    return (
        PropertySelectValue.objects.filter(multi_tenant_company=multi_tenant_company)
        .with_usage_count(multi_tenant_company_id=multi_tenant_company.id)
        .select_related("property", "image")
        .prefetch_related(
            "propertyselectvaluetranslation_set",
            "property__propertytranslation_set",
        )
    )


def resolve_property_ids(
    *,
    multi_tenant_company: MultiTenantCompany,
    property_id: int | None,
    property_internal_name: str | None = None,
    property_name: str | None = None,
) -> list[int] | None:
    if not any(
        [
            property_id is not None,
            property_internal_name,
            property_name,
        ]
    ):
        return None

    queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

    if property_id is not None:
        queryset = queryset.filter(id=property_id)

    if property_internal_name:
        queryset = queryset.filter(internal_name__iexact=property_internal_name)

    if property_name:
        queryset = queryset.filter(propertytranslation__name__iexact=property_name)

    return list(
        queryset.order_by("id").values_list("id", flat=True).distinct()[:2]
    )


def serialize_property_reference(*, property_instance: Property) -> PropertyReferencePayload:
    return {
        "id": property_instance.id,
        "name": property_instance.name,
        "internal_name": property_instance.internal_name,
        "type": property_instance.type,
        "type_label": property_instance.get_type_display(),
        "is_product_type": property_instance.is_product_type,
    }


def serialize_property_select_value_detail(
    *,
    select_value: PropertySelectValue,
) -> PropertySelectValueDetailPayload:
    property_instance = select_value.property
    value = select_value.value
    return {
        "id": select_value.id,
        "value": value,
        "full_value_name": f"{property_instance.name} > {value}",
        "usage_count": getattr(select_value, "usage_count", 0),
        "thumbnail_url": select_value.image.image_web_url if select_value.image else None,
        "property": serialize_property_reference(property_instance=property_instance),
        "translations": [
            {
                "language": translation.language,
                "value": translation.value,
            }
            for translation in select_value.propertyselectvaluetranslation_set.all()
        ],
    }


def serialize_property_select_value_summary(
    *,
    select_value: PropertySelectValue,
    include_translations: bool = False,
) -> PropertySelectValueSummaryPayload | PropertySelectValueDetailPayload:
    payload: PropertySelectValueSummaryPayload | PropertySelectValueDetailPayload = {
        "id": select_value.id,
        "value": select_value.value,
        "full_value_name": f"{select_value.property.name} > {select_value.value}",
        "usage_count": getattr(select_value, "usage_count", 0),
        "thumbnail_url": select_value.image.image_web_url if select_value.image else None,
        "property": serialize_property_reference(property_instance=select_value.property),
    }
    if include_translations:
        payload["translations"] = [
            {
                "language": translation.language,
                "value": translation.value,
            }
            for translation in select_value.propertyselectvaluetranslation_set.all()
        ]
    return payload


def serialize_property_select_value_search_result(
    *,
    select_value: PropertySelectValue,
    include_translations: bool = False,
    include_usage_count: bool = False,
) -> PropertySelectValueSearchResultPayload:
    payload: PropertySelectValueSearchResultPayload = {
        "id": select_value.id,
        "value": select_value.value,
        "thumbnail_url": select_value.image.image_web_url if select_value.image else None,
        "property": serialize_property_reference(property_instance=select_value.property),
    }
    if include_usage_count:
        payload["usage_count"] = getattr(select_value, "usage_count", 0)
    if include_translations:
        payload["translations"] = [
            {
                "language": translation.language,
                "value": translation.value,
            }
            for translation in select_value.propertyselectvaluetranslation_set.all()
        ]
    return payload


def serialize_property_detail(*, property_instance: Property) -> PropertyDetailPayload:
    return {
        "id": property_instance.id,
        "name": property_instance.name,
        "internal_name": property_instance.internal_name,
        "type": property_instance.type,
        "type_label": property_instance.get_type_display(),
        "is_public_information": property_instance.is_public_information,
        "add_to_filters": property_instance.add_to_filters,
        "has_image": property_instance.has_image,
        "is_product_type": property_instance.is_product_type,
        "translations": [
            {
                "language": translation.language,
                "name": translation.name,
            }
            for translation in property_instance.propertytranslation_set.all()
        ],
        "values": [
            {
                "id": property_value.id,
                "value": property_value.value,
                "translations": [
                    {
                        "language": translation.language,
                        "value": translation.value,
                    }
                    for translation in property_value.propertyselectvaluetranslation_set.all()
                ],
            }
            for property_value in property_instance.propertyselectvalue_set.all()
        ],
    }


def serialize_property_search_result(
    *,
    property_instance: Property,
    include_translations: bool = False,
) -> PropertySearchResultPayload:
    payload: PropertySearchResultPayload = {
        "id": property_instance.id,
        "name": property_instance.name,
        "internal_name": property_instance.internal_name,
        "type": property_instance.type,
        "type_label": property_instance.get_type_display(),
        "is_public_information": property_instance.is_public_information,
        "add_to_filters": property_instance.add_to_filters,
        "has_image": property_instance.has_image,
    }
    if include_translations:
        payload["translations"] = [
            {
                "language": translation.language,
                "name": translation.name,
            }
            for translation in property_instance.propertytranslation_set.all()
        ]
    return payload


def build_property_mutation_payload(
    *,
    property_instance: Property,
    created: bool,
) -> CreatePropertyPayload | EditPropertyPayload:
    payload = {
        "property_id": property_instance.id,
        "internal_name": property_instance.internal_name,
        "name": property_instance.name,
        "type": property_instance.type,
        "type_label": property_instance.get_type_display(),
        "message": "Saved successfully. Use get_property for details.",
    }
    if created:
        return {
            "created": True,
            **payload,
        }
    return {
        "updated": True,
        **payload,
    }


def build_select_value_mutation_payload(
    *,
    select_value: PropertySelectValue,
    created: bool,
) -> CreatePropertySelectValuePayload | EditPropertySelectValuePayload:
    payload = {
        "select_value_id": select_value.id,
        "property_id": select_value.property_id,
        "value": select_value.value,
        "full_value_name": f"{select_value.property.name} > {select_value.value}",
        "message": "Saved successfully. Use get_property_select_value for details.",
    }
    if created:
        return {
            "created": True,
            **payload,
        }
    return {
        "updated": True,
        **payload,
    }
