from decimal import Decimal

from strawberry.relay.utils import to_base64
from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, Annotated, lazy

from typing import List, Optional

from media.models import Media
from products.models import Product, BundleProduct, UmbrellaProduct, SimpleProduct, \
    ProductTranslation, ConfigurableVariation, BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, SupplierPrices
from taxes.schema.types.types import VatRateType
from units.schema.types.types import UnitType
from .filters import ProductFilter, BundleProductFilter, UmbrellaProductFilter, \
    SimpleProductFilter, ProductTranslationFilter, ConfigurableVariationFilter, BundleVariationFilter, BillOfMaterialFilter, SupplierProductFilter, \
    DropshipProductFilter, ManufacturableProductFilter, SupplierPricesFilter
from .ordering import ProductOrder, BundleProductOrder, UmbrellaProductOrder, \
    SimpleProductOrder, ProductTranslationOrder, ConfigurableVariationOrder, BundleVariationOrder, BillOfMaterialOrder, SupplierProductOrder, \
    DropshipProductOrder, ManufacturableProductOrder, SupplierPricesOrder


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    vat_rate: Optional[VatRateType]
    base_products: List[Annotated['ProductType', lazy("products.schema.types.types")]]

    supplier: Optional[CompanyType]

    @field()
    def proxy_id(self, info) -> str:
        if self.is_simple():
            graphql_type = SimpleProductType
        elif self.is_bundle():
            graphql_type = BundleProductType
        elif self.is_umbrella():
            graphql_type = UmbrellaProductType
        elif self.is_manufacturable():
            graphql_type = ManufacturableProductType
        elif self.is_dropship():
            graphql_type = DropshipProductType
        elif self.is_supplier_product():
            graphql_type = SupplierProductType
        else:
            graphql_type = ProductType

        return to_base64(graphql_type, self.pk)

    @field()
    def name(self, info) -> str | None:
        return self.name

    @field(description="Gets the URL of the first MediaProductThrough Image with the lowest sort order")
    def thumbnail_url(self, info) -> str | None:
        media_relation = self.mediaproductthrough_set.filter(media__type=Media.IMAGE).order_by('sort_order')

        first_media = media_relation.first()
        if first_media and first_media.media.image:
            return first_media.media.image_web_url()

        return None

    @field()
    def inventory_physical(self, info) -> str | None:
        return self.inventory.physical()

    @field()
    def inventory_salable(self, info) -> str | None:
        return self.inventory.salable()

    @field()
    def inventory_reserved(self, info) -> str | None:
        return self.inventory.reserved()


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


@type(ConfigurableVariation, filters=ConfigurableVariationFilter, order=ConfigurableVariationOrder, pagination=True, fields="__all__")
class ConfigurableVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]


@type(BillOfMaterial, filters=BillOfMaterialFilter, order=BillOfMaterialOrder, pagination=True, fields="__all__")
class BillOfMaterialType(relay.Node, GetQuerysetMultiTenantMixin):
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
    base_products: List[Annotated['ProductType', lazy("products.schema.types.types")]]

    @field()
    def name(self, info) -> str | None:
        return self.name

    @field()
    def quantity(self, info) -> int:
        return self.details.first().quantity if self.details.exists() else None

    @field()
    def unit_price(self, info) -> float:
        return self.details.first().unit_price if self.details.exists() else None

    @field()
    def unit(self, info) -> UnitType:
        unit = self.details.first().unit if self.details.exists() else None
        return unit

    @field()
    def proxy_id(self, info) -> str:
        return to_base64(ProductType, self.pk)


@type(SupplierPrices, filters=SupplierPricesFilter, order=SupplierPricesOrder, pagination=True, fields="__all__")
class SupplierPricesType(relay.Node, GetQuerysetMultiTenantMixin):
    supplier_product: SupplierProductType
    unit: UnitType
