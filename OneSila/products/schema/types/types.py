from decimal import Decimal

from strawberry.relay.utils import to_base64
from strawberry_django.relay import resolve_model_id

from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field

from typing import List, Optional

from products.models import Product, BundleProduct, UmbrellaProduct, SimpleProduct, \
    ProductTranslation, UmbrellaVariation, BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct
from taxes.schema.types.types import VatRateType
from units.schema.types.types import UnitType
from .filters import ProductFilter, BundleProductFilter, UmbrellaProductFilter, \
    SimpleProductFilter, ProductTranslationFilter, UmbrellaVariationFilter, BundleVariationFilter, BillOfMaterialFilter, SupplierProductFilter, \
    DropshipProductFilter, ManufacturableProductFilter
from .ordering import ProductOrder, BundleProductOrder, UmbrellaProductOrder, \
    SimpleProductOrder, ProductTranslationOrder, UmbrellaVariationOrder, BundleVariationOrder, BillOfMaterialOrder, SupplierProductOrder, \
    DropshipProductOrder, ManufacturableProductOrder


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    vat_rate: VatRateType

    @field()
    def proxy_id(self, info) -> str:
        if self.is_simple():
            graphql_type = SimpleProductType
        elif self.is_bundle():
            graphql_type = BundleProductType
        elif self.is_umbrella():
            graphql_type = UmbrellaProductType
        else:
            graphql_type = ProductType

        return to_base64(graphql_type, self.pk)

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass

@type(BundleProduct, filters=BundleProductFilter, order=BundleProductOrder, pagination=True, fields="__all__")
class BundleProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(UmbrellaProduct, filters=UmbrellaProductFilter, order=UmbrellaProductOrder, pagination=True, fields="__all__")
class UmbrellaProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(SimpleProduct, filters=SimpleProductFilter, order=SimpleProductOrder, pagination=True, fields="__all__")
class SimpleProductType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def name(self, info) -> str | None:
        return self.name

@type(UmbrellaVariation, filters=UmbrellaVariationFilter, order=UmbrellaVariationOrder, pagination=True, fields="__all__")
class UmbrellaVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]


@type(ManufacturableProduct, filters=ManufacturableProductFilter, order=ManufacturableProductOrder, pagination=True, fields="__all__")
class ManufacturableProductType(relay.Node, GetQuerysetMultiTenantMixin):
    production_time: Decimal

    @field()
    def name(self, info) -> str | None:
        return self.name

@type(DropshipProduct, filters=DropshipProductFilter, order=DropshipProductOrder, pagination=True, fields="__all__")
class DropshipProductType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def name(self, info) -> str | None:
        return self.name


@type(SupplierProduct, filters=SupplierProductFilter, order=SupplierProductOrder, pagination=True, fields="__all__")
class SupplierProductType(relay.Node, GetQuerysetMultiTenantMixin):
    supplier: Optional[CompanyType]
    unit: Optional[UnitType]
    product: ProductType
    quantity: int
    purchase_price: float

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(BillOfMaterial, filters=BillOfMaterialFilter, order=BillOfMaterialOrder, pagination=True, fields="__all__")
class BillOfMaterialType(relay.Node, GetQuerysetMultiTenantMixin):
    manufacturable: Optional[ProductType]
    component: Optional[ProductType]
    quantity: int
