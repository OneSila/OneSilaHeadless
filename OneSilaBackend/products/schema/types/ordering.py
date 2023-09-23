from core.schema.types.ordering import order
from core.schema.types.types import auto

from products.models import Product, BundleProduct, UmbrellaProduct, \
    ProductVariation, ProductTranslation, UmbrellaVariation, \
    BundleVariation


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


@order(ProductTranslation)
class ProductTranslationOrder:
    id: auto


@order(UmbrellaVariation)
class UmbrellaVariationOrder:
    id: auto


@order(BundleVariation)
class BundleVariationOrder:
    id: auto
