from typing import Optional

from contacts.schema.types.filters import SupplierFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy

from products.models import Product, BundleProduct, UmbrellaProduct, \
    SimpleProduct, ProductTranslation, UmbrellaVariation, BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, \
    SupplierPrices
from taxes.schema.types.filters import VatRateFilter
from units.schema.types.filters import UnitFilter


@filter(Product)
class ProductFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    id: auto
    sku: auto
    type: auto
    for_sale: auto
    vat_rate: Optional[VatRateFilter]
    exclude_demo_data: Optional[bool]

@filter(BundleProduct)
class BundleProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(UmbrellaProduct)
class UmbrellaProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(SimpleProduct)
class SimpleProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(ProductTranslation)
class ProductTranslationFilter:
    id: auto
    product: Optional[ProductFilter]
    language: auto


@filter(UmbrellaVariation)
class UmbrellaVariationFilter:
    id: auto
    umbrella: Optional[ProductFilter]


@filter(BundleVariation)
class BundleVariationFilter:
    id: auto
    umbrella: Optional[ProductFilter]

@filter(ManufacturableProduct)
class ManufacturableProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(DropshipProduct)
class DropshipProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(SupplierProduct)
class SupplierProductFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sku: auto
    supplier: Optional[SupplierFilter]
    base_products: Optional[lazy['ProductFilter', "products.schema.types.filters"]]



@filter(BillOfMaterial)
class BillOfMaterialFilter:
    id: auto
    umbrella: Optional[ProductFilter]

@filter(SupplierPrices)
class SupplierPricesFilter(SearchFilterMixin):
    search: str | None
    supplier_product: Optional[SupplierProductFilter]
