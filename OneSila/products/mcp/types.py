from __future__ import annotations

from typing import Literal

from typing_extensions import TypedDict

from properties.mcp.types import PropertyReferencePayload, PropertySelectValueSummaryPayload


ProductTypeValue = Literal["SIMPLE", "BUNDLE", "CONFIGURABLE", "ALIAS"]
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


class ProductImagePayload(TypedDict):
    image_url: str | None
    thumbnail_url: str | None
    type: str | None
    title: str | None
    description: str | None
    is_main_image: bool
    sort_order: int
    sales_channel_id: int | None


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
    title: str
    description: str
    type: str
    is_main_image: bool
    sort_order: int
    sales_channel_id: int


class ProductTranslationPayload(TypedDict, total=False):
    language: str
    name: str
    sales_channel: int | None
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


class ProductSummaryPayload(TypedDict):
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


class ProductDetailPayload(ProductSummaryPayload):
    allow_backorder: bool
    vat_rate_data: ProductVatRatePayload | None
    inspector: ProductInspectorPayload
    translations: list[ProductTranslationPayload]
    images: list[ProductImagePayload]
    properties: list[ProductAssignedPropertyPayload]
    prices: list[ProductPricePayload]


class SearchProductsPayload(TypedDict):
    total_count: int
    has_more: bool
    offset: int
    limit: int
    results: list[ProductSummaryPayload]


class ProductFrontendUrlPayload(TypedDict):
    id: int
    sku: str | None
    global_id: str
    frontend_path: str
    frontend_url: str


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


class ProductMutationPayload(TypedDict):
    updated: bool
    product: ProductDetailPayload


class ProductBatchMutationPayload(TypedDict):
    updated_count: int
    product: ProductDetailPayload


class CreateProductPayload(TypedDict):
    created: bool
    sku_was_generated: bool
    product: ProductDetailPayload
