from core.schema.types.ordering import order
from core.schema.types.types import auto

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation


@order(Product)
class ProductOrder:
    id: auto
    sku: auto


@order(BundleProduct)
class BundleProductOrder:
    id: auto
    sku: auto


@order(UmbrellaProduct)
class UmbrellaProductOrder:
    id: auto
    sku: auto


@order(ProductVariation)
class ProductVariationOrder:
    id: auto
    sku: auto
