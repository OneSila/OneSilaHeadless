from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ProductType, BundleProductType, UmbrellaProductType, \
    ProductVariationType, ProductTranslationType, UmbrellaVariationType, \
    BundleVariationType


@type(name="Query")
class ProductsQuery:
    product: ProductType = node()
    products: ListConnectionWithTotalCount[ProductType] = connection()

    bundle_product: BundleProductType = node()
    bundle_products: ListConnectionWithTotalCount[BundleProductType] = connection()

    unbrella_product: UmbrellaProductType = node()
    umbrella_products: ListConnectionWithTotalCount[UmbrellaProductType] = connection()

    product_variation: ProductVariationType = node()
    product_variations: ListConnectionWithTotalCount[ProductVariationType] = connection()

    product_translation: ProductTranslationType = node()
    product_translations: ListConnectionWithTotalCount[ProductTranslationType] = connection()

    umbrella_variation: UmbrellaVariationType = node()
    umbrella_variations: ListConnectionWithTotalCount[UmbrellaVariationType] = connection()

    bundle_variation: BundleVariationType = node()
    bundle_variations: ListConnectionWithTotalCount[BundleVariationType] = connection()
