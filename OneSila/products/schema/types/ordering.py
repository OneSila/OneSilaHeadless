from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from products.models import Product, BundleProduct, ConfigurableProduct, \
    SimpleProduct, ProductTranslation, ConfigurableVariation, \
    BundleVariation

@order(Product)
class ProductOrder:
    id: auto
    sku: auto
    created_at: auto
    updated_at: auto


@order(BundleProduct)
class BundleProductOrder:
    id: auto
    sku: auto


@order(ConfigurableProduct)
class ConfigurableProductOrder:
    id: auto
    sku: auto


@order(SimpleProduct)
class SimpleProductOrder:
    id: auto
    sku: auto


@order(ProductTranslation)
class ProductTranslationOrder:
    id: auto


@order(ConfigurableVariation)
class ConfigurableVariationOrder:
    id: auto


@order(BundleVariation)
class BundleVariationOrder:
    id: auto