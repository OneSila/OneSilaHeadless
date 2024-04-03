from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from products.models import Product, BundleProduct, UmbrellaProduct, \
    ProductVariation, ProductTranslation, UmbrellaVariation, BundleVariation


@filter(Product)
class ProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    type: auto
    vat_rate: auto


@filter(BundleProduct)
class BundleProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: auto


@filter(UmbrellaProduct)
class UmbrellaProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: auto


@filter(ProductVariation)
class ProductVariationFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: auto


@filter(ProductTranslation)
class ProductTranslationFilter:
    id: auto
    product: Optional[ProductFilter]
    language: auto


@filter(UmbrellaVariation)
class UmbrellaVariationFilter:
    id: auto
    umbrella: Optional[ProductFilter]


@filter(BundleVariation)
class BundleVariationFilter:
    id: auto
    umbrella: Optional[ProductFilter]
