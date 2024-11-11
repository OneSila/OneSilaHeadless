from typing import Optional

from django.db.models import Q
from strawberry import UNSET

from contacts.schema.types.filters import SupplierFilter
from core.managers import QuerySet
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy
from strawberry_django import filter_field as custom_filter
from products.models import Product, BundleProduct, ConfigurableProduct, \
    SimpleProduct, ProductTranslation, ConfigurableVariation, BundleVariation, BillOfMaterial, SupplierProduct, DropshipProduct, ManufacturableProduct, \
    SupplierPrices
from products_inspector.models import InspectorBlock
from taxes.schema.types.filters import VatRateFilter

@filter(Product)
class ProductFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    sku: auto
    type: auto
    for_sale: auto
    active: auto
    vat_rate: Optional[VatRateFilter]
    inspector: Optional[lazy['InspectorFilter', "products_inspector.schema.types.filters"]]

    @custom_filter
    def inspector_not_succefully_code_error(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            products_ids = InspectorBlock.objects.filter(successfully_checked=False, error_code=value).values_list('inspector__product_id', flat=True)
            queryset = queryset.filter(id__in=products_ids)

        return queryset, Q()


@filter(BundleProduct)
class BundleProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(ConfigurableProduct)
class ConfigurableProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(SimpleProduct)
class SimpleProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(ProductTranslation)
class ProductTranslationFilter:
    id: auto
    product: Optional[ProductFilter]
    language: auto


@filter(ConfigurableVariation)
class ConfigurableVariationFilter:
    id: auto
    parent: Optional[ProductFilter]


@filter(BundleVariation)
class BundleVariationFilter:
    id: auto
    parent: Optional[ProductFilter]


@filter(ManufacturableProduct)
class ManufacturableProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(DropshipProduct)
class DropshipProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]


@filter(SupplierProduct)
class SupplierProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    supplier: Optional[SupplierFilter]
    base_products: Optional[lazy['ProductFilter', "products.schema.types.filters"]]


@filter(BillOfMaterial)
class BillOfMaterialFilter:
    id: auto
    parent: Optional[ProductFilter]


@filter(SupplierPrices)
class SupplierPricesFilter(SearchFilterMixin):
    supplier_product: Optional[SupplierProductFilter]
