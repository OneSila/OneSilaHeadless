from typing import Optional

from django.db.models import Q
from strawberry import UNSET

from core.managers import QuerySet
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy
from strawberry_django import filter_field as custom_filter
from products.models import (
    Product,
    BundleProduct,
    ConfigurableProduct,
    SimpleProduct,
    ProductTranslation,
    ConfigurableVariation,
    BundleVariation,
    AliasProduct,
    ProductTranslationBulletPoint,
)
from products_inspector.models import InspectorBlock
from taxes.schema.types.filters import VatRateFilter
from strawberry.relay import from_base64


@filter(Product)
class ProductFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    sku: auto
    type: auto
    active: auto
    vat_rate: Optional[VatRateFilter]
    inspector: Optional[lazy['InspectorFilter', "products_inspector.schema.types.filters"]]

    @custom_filter
    def inspector_not_successfully_code_error(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            products_ids = InspectorBlock.objects.filter(successfully_checked=False, error_code=value).values_list('inspector__product_id', flat=True)
            queryset = queryset.filter(id__in=products_ids)

        return queryset, Q()

    @custom_filter
    def value_select_id(self, queryset: QuerySet, value: str, prefix: str) -> tuple[QuerySet, Q]:

        if value is not None:
            _, id = from_base64(value)
            queryset = queryset.filter(productproperty__value_select_id=id)

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


@filter(AliasProduct)
class AliasProductFilter(SearchFilterMixin):
    id: auto
    sku: auto
    vat_rate: Optional[VatRateFilter]
    alias_parent_product: Optional[ProductFilter]


@filter(ProductTranslation)
class ProductTranslationFilter:
    id: auto
    product: Optional[ProductFilter]
    language: auto
    sales_channel: Optional[lazy['SalesChannelFilter', "sales_channels.schema.types.filters"]]


@filter(ConfigurableVariation)
class ConfigurableVariationFilter:
    id: auto
    parent: Optional[ProductFilter]
    variation: Optional[ProductFilter]


@filter(BundleVariation)
class BundleVariationFilter:
    id: auto
    parent: Optional[ProductFilter]
    variation: Optional[ProductFilter]


@filter(ProductTranslationBulletPoint)
class ProductTranslationBulletPointFilter(SearchFilterMixin):
    id: auto
    product_translation: Optional[ProductTranslationFilter]
