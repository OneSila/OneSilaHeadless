from decimal import Decimal

from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from products.models import Product, BundleProduct, UmbrellaProduct, SimpleProduct, \
    ProductTranslation, UmbrellaVariation, BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, SupplierPrices
from units.schema.types.types import UnitType


@input(Product, fields="__all__")
class ProductInput:
    name: str


@partial(Product, fields="__all__")
class ProductPartialInput(NodeInput):
    pass


@input(BundleProduct, fields="__all__")
class BundleProductInput:
    pass


@partial(BundleProduct, fields="__all__")
class BundleProductPartialInput(NodeInput):
    pass


@input(UmbrellaProduct, fields="__all__")
class UmbrellaProductInput:
    pass


@partial(UmbrellaProduct, fields="__all__")
class UmbrellaProductPartialInput(NodeInput):
    pass


@input(SimpleProduct, fields="__all__")
class SimpleProductInput:
    pass


@partial(SimpleProduct, fields="__all__")
class SimpleProductPartialInput(NodeInput):
    pass


@input(ProductTranslation, fields="__all__")
class ProductTranslationInput:
    pass


@partial(ProductTranslation, fields="__all__")
class ProductTranslationPartialInput(NodeInput):
    pass


@input(UmbrellaVariation, fields="__all__")
class UmbrellaVariationInput:
    pass


@partial(UmbrellaVariation, fields="__all__")
class UmbrellaVariationPartialInput(NodeInput):
    pass


@input(BundleVariation, fields="__all__")
class BundleVariationInput:
    pass


@partial(BundleVariation, fields="__all__")
class BundleVariationPartialInput(NodeInput):
    pass


@input(ManufacturableProduct, fields="__all__")
class ManufacturableProductInput:
    pass


@partial(ManufacturableProduct, fields="__all__")
class ManufacturableProductPartialInput(NodeInput):
    pass


@input(DropshipProduct, fields="__all__")
class DropshipProductInput:
    pass


@partial(DropshipProduct, fields="__all__")
class DropshipProductPartialInput(NodeInput):
    pass


@input(SupplierProduct, fields="__all__")
class SupplierProductInput:
    name: str
    quantity: int
    unit_price: float
    unit: NodeInput


@partial(SupplierProduct, fields="__all__")
class SupplierProductPartialInput(NodeInput):
    quantity: int | None
    unit_price: float | None
    unit: NodeInput | None


@input(BillOfMaterial, fields="__all__")
class BillOfMaterialInput:
    pass


@partial(BillOfMaterial, fields="__all__")
class BillOfMaterialPartialInput(NodeInput):
    pass

@input(SupplierPrices, fields="__all__")
class SupplierPricesInput:
    pass


@partial(SupplierPrices, fields="__all__")
class SupplierPricesPartialInput(NodeInput):
    pass