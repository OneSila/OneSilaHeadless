from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, \
    BundleVariationType


@type(name="Query")
class ProductsQuery:
    product: ProductType = node()
    products: ListConnectionWithTotalCount[ProductType] = connection()

    bundle_product: BundleProductType = node()
    bundle_products: ListConnectionWithTotalCount[BundleProductType] = connection()

    configurable_product: ConfigurableProductType = node()
    configurable_products: ListConnectionWithTotalCount[ConfigurableProductType] = connection()

    simple_product: SimpleProductType = node()
    simple_products: ListConnectionWithTotalCount[SimpleProductType] = connection()

    product_translation: ProductTranslationType = node()
    product_translations: ListConnectionWithTotalCount[ProductTranslationType] = connection()

    configurable_variation: ConfigurableVariationType = node()
    configurable_variations: ListConnectionWithTotalCount[ConfigurableVariationType] = connection()

    bundle_variation: BundleVariationType = node()
    bundle_variations: ListConnectionWithTotalCount[BundleVariationType] = connection()