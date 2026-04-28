from __future__ import annotations

from typing import Literal

from typing_extensions import TypedDict

from properties.mcp.types import (
    CompanyLanguagesPayload,
    PropertyReferencePayload,
    PropertySelectValueSummaryPayload,
    PropertySelectValueTranslationPayload,
)


ProductTypeValue = Literal["SIMPLE", "BUNDLE", "CONFIGURABLE", "ALIAS"]
ProductRequirementTypeValue = Literal[
    "REQUIRED_IN_CONFIGURATOR",
    "OPTIONAL_IN_CONFIGURATOR",
    "REQUIRED",
    "OPTIONAL",
]
ProductValueScalar = str | int | float | bool | None
ProductValuePayload = ProductValueScalar | list[ProductValueScalar]


class ProductVatRatePayload(TypedDict):
    id: int
    name: str | None
    rate: int | None


class ProductInspectorIssuePayload(TypedDict):
    code: int
    title: str
    description: str
    fixing_message: str | None


class ProductInspectorPayload(TypedDict):
    has_inspector: bool
    has_missing_required_information: bool
    has_missing_optional_information: bool
    has_missing_information: bool
    status_code: int | None
    status_label: str | None
    issues: list[ProductInspectorIssuePayload]


class SalesChannelReferencePayload(TypedDict, total=False):
    id: int
    hostname: str
    active: bool
    type: str
    subtype: str | None
    views: list["SalesChannelViewSummaryPayload"]


class SalesChannelViewSummaryPayload(TypedDict):
    id: int
    name: str | None
    is_default: bool | None


class ProductWebsiteViewAssignPayload(TypedDict):
    id: int
    view_name: str | None
    remote_url: str | None


class ProductImagePayload(TypedDict):
    image_url: str | None
    thumbnail_url: str | None
    type: str | None
    title: str | None
    description: str | None
    is_main_image: bool
    sort_order: int
    sales_channel: SalesChannelReferencePayload | None


class ProductPricePayload(TypedDict):
    currency: str
    rrp: str | None
    price: str | None


class ProductPropertyTranslationInputPayload(TypedDict):
    language: str
    value: str


class ProductPropertyValueUpdateInputPayload(TypedDict, total=False):
    property_id: int
    property_internal_name: str
    value: ProductValuePayload
    value_is_id: bool
    translations: list[ProductPropertyTranslationInputPayload]


class ProductImageInputPayload(TypedDict, total=False):
    image_url: str
    image_content: str
    title: str
    description: str
    type: str
    is_main_image: bool
    sort_order: int
    sales_channel_id: int


class ProductTranslationUpsertInputPayload(TypedDict, total=False):
    language: str
    sales_channel_id: int
    name: str
    subtitle: str
    short_description: str
    description: str
    bullet_points: list[str]


class ProductPriceUpsertInputPayload(TypedDict, total=False):
    currency: str
    price: str | float | int
    rrp: str | float | int | None


class CreateProductInputPayload(TypedDict, total=False):
    type: ProductTypeValue
    name: str
    sku: str
    product_type_id: int
    product_type_value: str
    vat_rate_id: int
    vat_rate: int
    active: bool
    ean_code: str
    translations: list[ProductTranslationUpsertInputPayload]
    prices: list[ProductPriceUpsertInputPayload]
    properties: list[ProductPropertyValueUpdateInputPayload]
    images: list[ProductImageInputPayload]
    sales_channel_view_ids: list[int]


class UpsertProductInputPayload(TypedDict, total=False):
    product_id: int
    sku: str
    vat_rate_id: int
    vat_rate: int
    active: bool
    ean_code: str
    translations: list[ProductTranslationUpsertInputPayload]
    prices: list[ProductPriceUpsertInputPayload]
    properties: list[ProductPropertyValueUpdateInputPayload]
    images: list[ProductImageInputPayload]
    sales_channel_view_ids: list[int]
    workflows: list["WorkflowStateUpdateInputPayload"]


class WorkflowStateUpdateInputPayload(TypedDict):
    workflow_code: str
    state_code: str


class ProductTranslationPayload(TypedDict, total=False):
    language: str
    name: str
    sales_channel: SalesChannelReferencePayload | None
    subtitle: str
    short_description: str
    description: str
    url_key: str
    bullet_points: list[str]


class ProductAssignedPropertyValueTranslationPayload(TypedDict):
    language: str
    value: ProductValueScalar


class ProductAssignedPropertyValuePayload(TypedDict):
    id: int | None
    value: ProductValueScalar
    translations: list[ProductAssignedPropertyValueTranslationPayload]


class ProductAssignedPropertyPayload(TypedDict):
    property: PropertyReferencePayload
    value: ProductValuePayload
    values: list[ProductAssignedPropertyValuePayload]


class ProductRequirementProductTypePayload(TypedDict):
    id: int
    select_value: str


class ProductPropertyRequirementPayload(TypedDict):
    property_id: int
    property_name: str
    requirement_type: ProductRequirementTypeValue
    effectively_required: bool
    has_value: bool
    current_value_summary: str | None


class ProductPropertyRequirementsPayload(TypedDict):
    product_type: ProductRequirementProductTypePayload | None
    requirements: dict[str, ProductPropertyRequirementPayload]


class ProductSearchSummaryPayload(TypedDict):
    id: int
    sku: str | None
    name: str
    type: ProductTypeValue
    type_label: str
    active: bool
    vat_rate: int | None
    thumbnail_url: str | None
    has_images: bool
    has_missing_required_information: bool
    has_missing_optional_information: bool
    has_missing_information: bool
    workflows: list["ProductWorkflowAssignmentPayload"]


class WorkflowStateReferencePayload(TypedDict):
    id: int
    name: str
    code: str
    is_default: bool


class ProductWorkflowAssignmentPayload(TypedDict):
    workflow_id: int
    workflow_name: str
    workflow_code: str
    state: WorkflowStateReferencePayload


class ProductBaseDetailPayload(TypedDict):
    id: int
    sku: str | None
    name: str
    type: ProductTypeValue
    type_label: str
    active: bool
    ean_code: str | None
    vat_rate: int | None
    thumbnail_url: str | None
    has_images: bool
    onesila_url: str
    allow_backorder: bool


class ProductBrandVoiceLanguagePromptPayload(TypedDict):
    language: str
    prompt: str


class ProductBrandVoicePayload(TypedDict, total=False):
    brand_value_id: int
    brand_value: str
    default_prompt: str
    language_prompts: list[ProductBrandVoiceLanguagePromptPayload]


class ProductDetailPayload(ProductBaseDetailPayload, total=False):
    vat_rate_data: ProductVatRatePayload | None
    inspector: ProductInspectorPayload
    website_views_assign: list[ProductWebsiteViewAssignPayload]
    property_requirements: ProductPropertyRequirementsPayload
    translations: list[ProductTranslationPayload]
    images: list[ProductImagePayload]
    properties: list[ProductAssignedPropertyPayload]
    prices: list[ProductPricePayload]
    brand_voice: ProductBrandVoicePayload | None


class SearchProductsPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[ProductSearchSummaryPayload]


class VatRateOptionPayload(TypedDict):
    id: int
    name: str | None
    rate: int | None


class GetProductTypesPayload(TypedDict):
    count: int
    property: PropertyReferencePayload
    results: list[PropertySelectValueSummaryPayload]


class GetVatRatesPayload(TypedDict):
    count: int
    results: list[VatRateOptionPayload]


class CompanyProductTypePayload(TypedDict, total=False):
    id: int
    value: str
    translations: list[PropertySelectValueTranslationPayload]
    usage_count: int


class CompanyProductTypesPayload(TypedDict):
    count: int
    property: PropertyReferencePayload
    results: list[CompanyProductTypePayload]


class CompanyCurrencyPayload(TypedDict):
    id: int
    iso_code: str
    name: str
    symbol: str
    is_default: bool
    inherits_from_iso_code: str | None


class CompanyCurrenciesPayload(TypedDict):
    count: int
    default_currency_code: str | None
    results: list[CompanyCurrencyPayload]


class CompanyWorkflowPayload(TypedDict):
    id: int
    name: str
    code: str
    states: list[WorkflowStateReferencePayload]


class CompanyWorkflowsPayload(TypedDict):
    count: int
    results: list[CompanyWorkflowPayload]


class CompanyDetailsPayload(TypedDict, total=False):
    message: str
    languages: CompanyLanguagesPayload
    product_types: CompanyProductTypesPayload
    vat_rates: GetVatRatesPayload
    currencies: CompanyCurrenciesPayload
    workflows: CompanyWorkflowsPayload


class SearchSalesChannelsPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[SalesChannelReferencePayload]


class ProductUpsertAppliedUpdatesPayload(TypedDict, total=False):
    active: bool
    vat_rate: bool
    ean_code: bool
    translations: int
    prices: int
    properties: int
    images: int
    website_views_assignments: int
    workflows: int


class ProductUpsertPayload(TypedDict, total=False):
    updated: bool
    product_id: int
    sku: str | None
    name: str
    active: bool
    message: str
    applied_updates: ProductUpsertAppliedUpdatesPayload


class CreateProductPayload(TypedDict, total=False):
    created: bool
    sku_was_generated: bool
    product_id: int
    sku: str | None
    name: str
    message: str


class CreateProductsPayload(TypedDict):
    requested_count: int
    processed_count: int
    created_count: int
    results: list[CreateProductPayload]


class UpsertProductsPayload(TypedDict):
    requested_count: int
    processed_count: int
    updated_count: int
    results: list[ProductUpsertPayload]
