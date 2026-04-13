from __future__ import annotations

from typing import Literal

from typing_extensions import TypedDict


PropertyTypeValue = Literal[
    "INT",
    "FLOAT",
    "TEXT",
    "DESCRIPTION",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "SELECT",
    "MULTISELECT",
]


class PropertyTranslationPayload(TypedDict):
    language: str
    name: str


class PropertyTranslationInputPayload(TypedDict):
    language: str
    name: str


class CompanyLanguagePayload(TypedDict):
    code: str
    name: str
    name_local: str
    name_translated: str
    bidi: bool
    is_default: bool


class CompanyLanguagesPayload(TypedDict):
    default_language_code: str
    enabled_languages: list[CompanyLanguagePayload]


class PropertySelectValueTranslationPayload(TypedDict):
    language: str
    value: str


class PropertySelectValueTranslationInputPayload(TypedDict):
    language: str
    value: str


class PropertyValuePayload(TypedDict):
    id: int
    value: str
    translations: list[PropertySelectValueTranslationPayload]


class PropertySummaryPayload(TypedDict):
    id: int
    name: str
    internal_name: str | None
    type: PropertyTypeValue
    type_label: str
    is_public_information: bool
    add_to_filters: bool
    has_image: bool


class PropertyDetailPayload(PropertySummaryPayload):
    is_product_type: bool
    translations: list[PropertyTranslationPayload]
    values: list[PropertyValuePayload]


class SearchPropertiesPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[PropertySummaryPayload]


class PropertyReferencePayload(TypedDict):
    id: int
    name: str
    internal_name: str | None
    type: PropertyTypeValue
    type_label: str
    is_product_type: bool


class PropertySelectValueSummaryPayload(TypedDict):
    id: int
    value: str
    full_value_name: str
    usage_count: int
    thumbnail_url: str | None
    property: PropertyReferencePayload
    translations: list[PropertySelectValueTranslationPayload]


class PropertySelectValueDetailPayload(PropertySelectValueSummaryPayload):
    pass


class SearchPropertySelectValuesPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[PropertySelectValueSummaryPayload]


class RecommendPropertyTypePayload(TypedDict):
    recommended_type: PropertyTypeValue
    recommended_type_label: str
    requires_confirmation: bool
    message: str
    name: str | None
    internal_name: str | None


class CreatePropertyPayload(TypedDict):
    created: bool
    property: PropertyDetailPayload


class EditPropertyPayload(TypedDict):
    updated: bool
    property: PropertyDetailPayload


class CreatePropertySelectValuePayload(TypedDict):
    created: bool
    select_value: PropertySelectValueDetailPayload


class EditPropertySelectValuePayload(TypedDict):
    updated: bool
    select_value: PropertySelectValueDetailPayload
