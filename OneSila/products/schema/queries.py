from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import ProductType, BundleProductType, UmbrellaProductType, \
    SimpleProductType, ProductTranslationType, UmbrellaVariationType, \
    BundleVariationType, ManufacturableProductType, DropshipProductType, SupplierProductType, BillOfMaterialType, SupplierPricesType


@type(name="Query")
class ProductsQuery:
    product: ProductType = node()
    products: ListConnectionWithTotalCount[ProductType] = connection()

    bundle_product: BundleProductType = node()
    bundle_products: ListConnectionWithTotalCount[BundleProductType] = connection()

    unbrella_product: UmbrellaProductType = node()
    umbrella_products: ListConnectionWithTotalCount[UmbrellaProductType] = connection()

    simple_product: SimpleProductType = node()
    simple_products: ListConnectionWithTotalCount[SimpleProductType] = connection()

    product_translation: ProductTranslationType = node()
    product_translations: ListConnectionWithTotalCount[ProductTranslationType] = connection()

    umbrella_variation: UmbrellaVariationType = node()
    umbrella_variations: ListConnectionWithTotalCount[UmbrellaVariationType] = connection()

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

    supplier_price: SupplierPricesType = node()
    supplier_prices: ListConnectionWithTotalCount[SupplierPricesType] = connection()