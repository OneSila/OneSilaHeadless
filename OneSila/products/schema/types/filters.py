from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from products.models import Product, BundleProduct, UmbrellaProduct, \
    ProductVariation, ProductTranslation, UmbrellaVariation, BundleVariation


@filter(Product)
class ProductFilter:
    id: auto
    sku: auto
    type: auto
    tax_rate: auto


@filter(BundleProduct)
class BundleProductFilter:
    id: auto
    sku: auto
    tax_rate: auto


@filter(UmbrellaProduct)
class UmbrellaProductFilter:
    id: auto
    sku: auto
    tax_rate: auto


@filter(ProductVariation)
class ProductVariationFilter:
    id: auto
    sku: auto
    tax_rate: auto


@filter(ProductTranslation)
class ProductTranslationFilter:
    id: auto


@filter(UmbrellaVariation)
class UmbrellaVariationFilter:
    id: auto


@filter(BundleVariation)
class BundleVariationFilter:
    id: auto
