from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, \
    BundleVariationType, ManufacturableProductType, DropshipProductType, SupplierProductType, BillOfMaterialType, SupplierPriceType


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

    manufacturable_product: ManufacturableProductType = node()
    manufacturable_products: ListConnectionWithTotalCount[ManufacturableProductType] = connection()

    dropship_product: DropshipProductType = node()
    dropship_products: ListConnectionWithTotalCount[DropshipProductType] = connection()

    supplier_product: SupplierProductType = node()
    supplier_products: ListConnectionWithTotalCount[SupplierProductType] = connection()

    bill_of_material: BillOfMaterialType = node()
    bill_of_materials: ListConnectionWithTotalCount[BillOfMaterialType] = connection()

    supplier_price: SupplierPriceType = node()
    supplier_prices: ListConnectionWithTotalCount[SupplierPriceType] = connection()
