from typing import Optional

from django.db.models import Q, Exists, OuterRef, Subquery, Count
from strawberry import UNSET

from core.managers import QuerySet
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy, AnnotationMergerMixin
from strawberry_django import filter_field as custom_filter
from products.schema.types.content_filters import ProductContentFieldFilterMixin
from products.schema.types.media_filters import ProductMediaFilterMixin
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
from eancodes.models import EanCode
from sales_prices.models import SalesPrice, SalesPriceListItem
from sales_channels.integrations.amazon.models import (
    AmazonProductIssue,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
)
from sales_channels.integrations.ebay.models import EbayCategory, EbayProductCategory
from sales_channels.integrations.shein.models import SheinCategory, SheinProductCategory
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct
from taxes.schema.types.filters import VatRateFilter
from strawberry.relay import from_base64
from core.schema.core.types.filters import TimeStampRangeFilterMixin
from products.product_types import CONFIGURABLE


class ProductPropertyGlobalIdFilterMixin(AnnotationMergerMixin):
    value_select_id: Optional[str]
    value_select_ids: Optional[list[str]]
    property_id: Optional[str]

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

        for select_id in set(select_ids):
            queryset = queryset.filter(productproperty__value_select_id=select_id)

        return queryset, Q()

    @custom_filter
    def property_id(self, queryset: QuerySet, value: str, prefix: str) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, property_id = from_base64(value)
        condition = Q(productproperty__property_id=property_id)

        return queryset, condition


@filter(Product)
class ProductFilter(
    SearchFilterMixin,
    ExcluideDemoDataFilterMixin,
    TimeStampRangeFilterMixin,
    ProductPropertyGlobalIdFilterMixin,
    ProductContentFieldFilterMixin,
    ProductMediaFilterMixin,
):
    id: auto
    sku: auto
    type: auto
    active: auto
    allow_backorder: auto
    vat_rate: Optional[VatRateFilter]
    created_at: auto
    updated_at: auto
    inspector: Optional[lazy['InspectorFilter', "products_inspector.schema.types.filters"]]
    alias_parent_product: Optional[lazy["ProductFilter", "products.schema.types.filters"]]

    @staticmethod
    def _present_on_store_qs(*, sales_channel_id: str):
        return RemoteProduct.objects.filter(
            sales_channel_id=sales_channel_id,
            successfully_created=True,
            local_instance_id=OuterRef("pk"),
        )

    @staticmethod
    def _amazon_browser_node_qs(*, amazon_browse_node_id: str):
        browse_node_qs = AmazonBrowseNode.objects.filter(pk=amazon_browse_node_id)
        return AmazonProductBrowseNode.objects.filter(
            product_id=OuterRef("pk"),
            recommended_browse_node_id=Subquery(browse_node_qs.values("remote_id")[:1]),
            view__amazonsaleschannelview__remote_id=Subquery(browse_node_qs.values("marketplace_id")[:1]),
        )

    @staticmethod
    def _ebay_product_category_qs(*, ebay_category_id: str):
        category_qs = EbayCategory.objects.filter(pk=ebay_category_id)
        return EbayProductCategory.objects.filter(
            product_id=OuterRef("pk"),
            remote_id=Subquery(category_qs.values("remote_id")[:1]),
            view__ebaysaleschannelview__default_category_tree_id=Subquery(category_qs.values("marketplace_default_tree_id")[:1]),
        )

    @staticmethod
    def _shein_product_category_qs(*, shein_category_id: str):
        category_qs = SheinCategory.objects.filter(pk=shein_category_id)
        return SheinProductCategory.objects.filter(
            product_id=OuterRef("pk"),
            remote_id=Subquery(category_qs.values("remote_id")[:1]),
        )

    @custom_filter
    def has_ean_codes(
        self,
        *,
        queryset: QuerySet,
        value: bool,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        ean_codes_qs = EanCode.objects.filter(
            product_id=OuterRef("pk"),
            ean_code__isnull=False,
        )
        queryset = queryset.annotate(
            has_ean_code=Exists(ean_codes_qs)
        ).filter(has_ean_code=value)

        return queryset, Q()

    @custom_filter
    def has_alias_products(
        self,
        *,
        queryset: QuerySet,
        value: bool,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        alias_products_qs = Product.objects.filter(
            alias_parent_product_id=OuterRef("pk"),
        )
        queryset = queryset.annotate(
            has_alias_products=Exists(alias_products_qs)
        ).filter(has_alias_products=value)

        return queryset, Q()

    @custom_filter
    def has_multiple_configurable_parents(
        self,
        *,
        queryset: QuerySet,
        value: bool,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        multiple_parents_qs = (
            ConfigurableVariation.objects.filter(
                variation_id=OuterRef("pk"),
            )
            .values("variation_id")
            .annotate(parent_count=Count("parent_id", distinct=True))
            .filter(parent_count__gt=1)
        )
        queryset = queryset.annotate(
            has_multiple_configurable_parents=Exists(multiple_parents_qs)
        ).filter(has_multiple_configurable_parents=value)

        return queryset, Q()

    @custom_filter
    def variation_of_product_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, variation_id = from_base64(value)
        parent_qs = ConfigurableVariation.objects.filter(
            parent_id=OuterRef("pk"),
            variation_id=variation_id,
        )
        queryset = queryset.annotate(
            is_configurable_parent_for_variation=Exists(parent_qs)
        ).filter(is_configurable_parent_for_variation=True)

        return queryset, Q()

    @custom_filter
    def is_multiple_parent(
        self,
        *,
        queryset: QuerySet,
        value: bool,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        parent_variations_qs = ConfigurableVariation.objects.filter(
            multi_tenant_company_id=OuterRef("multi_tenant_company_id"),
            parent_id=OuterRef("pk"),
        )
        other_parent_same_variation_qs = ConfigurableVariation.objects.filter(
            multi_tenant_company_id=OuterRef("multi_tenant_company_id"),
            variation_id=OuterRef("variation_id"),
        ).exclude(
            parent_id=OuterRef("parent_id"),
        )
        shared_parent_qs = parent_variations_qs.annotate(
            has_other_parent=Exists(other_parent_same_variation_qs)
        ).filter(
            has_other_parent=True
        )

        queryset = queryset.filter(type=CONFIGURABLE).annotate(
            is_multiple_parent=Exists(shared_parent_qs)
        )

        if value:
            first_shared_variation_qs = (
                parent_variations_qs.annotate(
                    has_other_parent=Exists(other_parent_same_variation_qs)
                )
                .filter(has_other_parent=True)
                .order_by("variation_id")
                .values("variation_id")[:1]
            )
            queryset = queryset.filter(is_multiple_parent=True).annotate(
                first_shared_variation_id=Subquery(first_shared_variation_qs)
            ).order_by("first_shared_variation_id", "id")
        else:
            queryset = queryset.filter(is_multiple_parent=False)

        return queryset, Q()

    @custom_filter
    def has_prices_for_currency(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, currency_id = from_base64(value)
        prices_qs = SalesPrice.objects.filter(
            product_id=OuterRef("pk"),
            currency_id=currency_id,
        ).filter(
            Q(price__isnull=False) | Q(rrp__isnull=False)
        )
        queryset = queryset.annotate(
            has_prices_for_currency=Exists(prices_qs)
        ).filter(has_prices_for_currency=True)

        return queryset, Q()

    @custom_filter
    def missing_prices_for_currency(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, currency_id = from_base64(value)
        prices_qs = SalesPrice.objects.filter(
            product_id=OuterRef("pk"),
            currency_id=currency_id,
        ).filter(
            Q(price__isnull=False) | Q(rrp__isnull=False)
        )
        queryset = queryset.annotate(
            has_prices_for_currency=Exists(prices_qs)
        ).filter(has_prices_for_currency=False)

        return queryset, Q()

    @custom_filter
    def has_price_list(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, price_list_id = from_base64(value)
        items_qs = SalesPriceListItem.objects.filter(
            product_id=OuterRef("pk"),
            salespricelist_id=price_list_id,
        ).filter(
            Q(price_auto__isnull=False) | Q(price_override__isnull=False)
        )
        queryset = queryset.annotate(
            has_price_list=Exists(items_qs)
        ).filter(has_price_list=True)

        return queryset, Q()

    @custom_filter
    def missing_price_list(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, price_list_id = from_base64(value)
        items_qs = SalesPriceListItem.objects.filter(
            product_id=OuterRef("pk"),
            salespricelist_id=price_list_id,
        ).filter(
            Q(price_auto__isnull=False) | Q(price_override__isnull=False)
        )
        queryset = queryset.annotate(
            has_price_list=Exists(items_qs)
        ).filter(has_price_list=False)

        return queryset, Q()

    @custom_filter
    def amazon_browser_node_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, amazon_browse_node_id = from_base64(value)
        queryset = queryset.annotate(
            has_amazon_browser_node=Exists(
                self._amazon_browser_node_qs(amazon_browse_node_id=amazon_browse_node_id)
            )
        ).filter(has_amazon_browser_node=True)

        return queryset, Q()

    @custom_filter
    def exclude_amazon_browser_node_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, amazon_browse_node_id = from_base64(value)
        queryset = queryset.annotate(
            has_amazon_browser_node=Exists(
                self._amazon_browser_node_qs(amazon_browse_node_id=amazon_browse_node_id)
            )
        ).filter(has_amazon_browser_node=False)

        return queryset, Q()

    @custom_filter
    def ebay_product_category_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, ebay_category_id = from_base64(value)
        queryset = queryset.annotate(
            has_ebay_product_category=Exists(
                self._ebay_product_category_qs(ebay_category_id=ebay_category_id)
            )
        ).filter(has_ebay_product_category=True)

        return queryset, Q()

    @custom_filter
    def exclude_ebay_product_category_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, ebay_category_id = from_base64(value)
        queryset = queryset.annotate(
            has_ebay_product_category=Exists(
                self._ebay_product_category_qs(ebay_category_id=ebay_category_id)
            )
        ).filter(has_ebay_product_category=False)

        return queryset, Q()

    @custom_filter
    def shein_product_category_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, shein_category_id = from_base64(value)
        queryset = queryset.annotate(
            has_shein_product_category=Exists(
                self._shein_product_category_qs(shein_category_id=shein_category_id)
            )
        ).filter(has_shein_product_category=True)

        return queryset, Q()

    @custom_filter
    def exclude_shein_product_category_id(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        _, shein_category_id = from_base64(value)
        queryset = queryset.annotate(
            has_shein_product_category=Exists(
                self._shein_product_category_qs(shein_category_id=shein_category_id)
            )
        ).filter(has_shein_product_category=False)

        return queryset, Q()

    @custom_filter
    def inspector_not_successfully_code_error(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value in (None, UNSET):
            return queryset, Q()

        error_blocks_qs = InspectorBlock.objects.filter(
            inspector__product_id=OuterRef("pk"),
            successfully_checked=False,
            error_code=value,
        )

        queryset = queryset.annotate(
            has_inspector_not_successfully_code_error=Exists(error_blocks_qs)
        )
        return queryset, Q(has_inspector_not_successfully_code_error=True)

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
    def present_on_store_sales_channel_id(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value in (None, UNSET):
            return queryset, Q()

        _, sales_channel_id = from_base64(value)
        queryset = queryset.annotate(
            present_on_store=Exists(self._present_on_store_qs(sales_channel_id=sales_channel_id))
        ).filter(present_on_store=True)
        return queryset, Q()

    @custom_filter
    def not_present_on_store_sales_channel_id(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) -> tuple[QuerySet, Q]:

        if value in (None, UNSET):
            return queryset, Q()

        _, sales_channel_id = from_base64(value)
        queryset = queryset.annotate(
            present_on_store=Exists(self._present_on_store_qs(sales_channel_id=sales_channel_id))
        ).filter(present_on_store=False)
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
