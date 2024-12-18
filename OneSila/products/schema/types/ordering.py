from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from products.models import Product, BundleProduct, ConfigurableProduct, \
    SimpleProduct, ProductTranslation, ConfigurableVariation, \
    BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, SupplierPrice


@order(Product)
class ProductOrder:
    id: auto
    sku: auto


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


@order(SupplierPrice)
class SupplierPriceOrder:
    id: auto
    quantity: auto
    unit_price: auto
