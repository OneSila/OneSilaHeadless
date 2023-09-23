from core.schema.types.types import auto
from core.schema.types.filters import filter

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation


@filter(Product)
class ProductFilter:
    id: auto
    sku: auto
    type: auto
    tax_rate: auto


@filter(BundleProduct)
class Filter:
    id: auto
    sku: auto
    tax_rate: auto


@filter(UmbrellaProduct)
class Filter:
    id: auto
    sku: auto
    tax_rate: auto


@filter(ProductVariation)
class Filter:
    id: auto
    sku: auto
    tax_rate: auto
