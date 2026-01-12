from typing import Optional

from django.db.models import Q, Exists, OuterRef
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
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonProductIssue
from sales_channels.models import SalesChannelViewAssign
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
        if value in (None, UNSET):
            return queryset, Q()

        _, select_id = from_base64(value)
        condition = Q(productproperty__value_select_id=select_id)

        return queryset, condition

    @custom_filter
    def value_select_ids(self, queryset: QuerySet, value: list[str], prefix: str) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        select_ids = [from_base64(item)[1] for item in value if item not in (None, UNSET)]
        if not select_ids:
            return queryset, Q()

        condition = Q(productproperty__value_select_id__in=select_ids)

        return queryset, condition

    @custom_filter
    def amazon_products_with_issues_for_sales_channel(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            _, sales_channel_id = from_base64(value)
            issues_qs = AmazonProductIssue.objects.filter(
                remote_product__local_instance=OuterRef("pk"),
                remote_product__sales_channel_id=sales_channel_id,
            )

            # Keep only products that have a matching issue
            queryset = queryset.annotate(
                has_issue=Exists(issues_qs)
            ).filter(has_issue=True)

        return queryset, Q()

    @custom_filter
    def assigned_to_sales_channel_view_id(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            _, view_id = from_base64(value)
            assigns_qs = SalesChannelViewAssign.objects.filter(
                product_id=OuterRef("pk"),
                sales_channel_view_id=view_id,
            )
            queryset = queryset.annotate(
                assigned_to_view=Exists(assigns_qs)
            ).filter(assigned_to_view=True)

        return queryset, Q()

    @custom_filter
    def not_assigned_to_sales_channel_view_id(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            _, view_id = from_base64(value)
            assigns_qs = SalesChannelViewAssign.objects.filter(
                product_id=OuterRef("pk"),
                sales_channel_view_id=view_id,
            )
            queryset = queryset.annotate(
                assigned_to_view=Exists(assigns_qs)
            ).filter(assigned_to_view=False)

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
