from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, \
    BundleVariationType


@type(name="Query")
class ProductsQuery:
    product: ProductType = node()
    products: DjangoListConnection[ProductType] = connection()

    bundle_product: BundleProductType = node()
    bundle_products: DjangoListConnection[BundleProductType] = connection()

    configurable_product: ConfigurableProductType = node()
    configurable_products: DjangoListConnection[ConfigurableProductType] = connection()

    simple_product: SimpleProductType = node()
    simple_products: DjangoListConnection[SimpleProductType] = connection()

    product_translation: ProductTranslationType = node()
    product_translations: DjangoListConnection[ProductTranslationType] = connection()

    configurable_variation: ConfigurableVariationType = node()
    configurable_variations: DjangoListConnection[ConfigurableVariationType] = connection()

    bundle_variation: BundleVariationType = node()
    bundle_variations: DjangoListConnection[BundleVariationType] = connection()
