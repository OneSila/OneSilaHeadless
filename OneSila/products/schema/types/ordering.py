from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from products.models import Product, BundleProduct, UmbrellaProduct, \
    SimpleProduct, ProductTranslation, UmbrellaVariation, \
    BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, SupplierPrices


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


@order(SimpleProduct)
class SimpleProductOrder:
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

@order(ManufacturableProduct)
class ManufacturableProductOrder:
    id: auto
    sku: auto


@order(DropshipProduct)
class DropshipProductOrder:
    id: auto
    sku: auto


@order(SupplierProduct)
class SupplierProductOrder:
    id: auto
    sku: auto


@order(BillOfMaterial)
class BillOfMaterialOrder:
    id: auto

@order(SupplierPrices)
class SupplierPricesOrder:
    id: auto
    quantity: auto
    unit_price: auto