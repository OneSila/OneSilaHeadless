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


class PropertySearchResultPayload(PropertySummaryPayload, total=False):
    translations: list[PropertyTranslationPayload]


class PropertyDetailPayload(PropertySummaryPayload):
    is_product_type: bool
    translations: list[PropertyTranslationPayload]
    values: list[PropertyValuePayload]


class SearchPropertiesPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[PropertySearchResultPayload]


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


class PropertySelectValueDetailPayload(PropertySelectValueSummaryPayload):
    translations: list[PropertySelectValueTranslationPayload]


class PropertySelectValueSearchResultPayload(TypedDict, total=False):
    id: int
    value: str
    thumbnail_url: str | None
    property: PropertyReferencePayload
    usage_count: int
    translations: list[PropertySelectValueTranslationPayload]


class SearchPropertySelectValuesPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[PropertySelectValueSearchResultPayload]


class CreatePropertyPayload(TypedDict):
    created: bool
    property_id: int
    internal_name: str | None
    name: str
    type: PropertyTypeValue
    type_label: str
    message: str


class EditPropertyPayload(TypedDict):
    updated: bool
    property_id: int
    internal_name: str | None
    name: str
    type: PropertyTypeValue
    type_label: str
    message: str


class CreatePropertySelectValuePayload(TypedDict):
    created: bool
    select_value_id: int
    property_id: int
    value: str
    full_value_name: str
    message: str


class EditPropertySelectValuePayload(TypedDict):
    updated: bool
    select_value_id: int
    property_id: int
    value: str
    full_value_name: str
    message: str
