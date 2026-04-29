from typing import Optional

from core.managers import QuerySet
from core.schema.core.types.types import auto
from core.schema.core.types.filters import custom_filter, filter, SearchFilterMixin, lazy
from django.db.models import Q
from strawberry import UNSET
from products.schema.types.filters import ProductFilter

from sales_channels.models import (
    ImportCurrency,
    ImportImage,
    SalesChannelImport,
    SalesChannelFeed,
    SalesChannelFeedItem,
    ImportProduct,
    ImportProperty,
    ImportPropertySelectValue,
    ImportVat,
    RemoteCategory,
    RemoteCurrency,
    RemoteCustomer,
    RemoteImage,
    RemoteImageProductAssociation,
    RemoteLog,
    RemoteOrder,
    RemoteProduct,
    RemoteProductContent,
    RemoteProductProperty,
    SyncRequest,
    RemoteProperty,
    RemoteDocumentType,
    RemotePropertySelectValue,
    RemoteVat,
    SalesChannel,
    SalesChannelIntegrationPricelist,
    SalesChannelView,
    SalesChannelViewAssign,
    RejectedSalesChannelViewAssign,
    SalesChannelContentTemplate,
    ManualSalesChannel,
    ManualSalesChannelView,
)
from sales_channels.models.sales_channels import RemoteLanguage


@filter(ImportCurrency)
class ImportCurrencyFilter(SearchFilterMixin):
    id: auto


@filter(ImportImage)
class ImportImageFilter(SearchFilterMixin):
    id: auto


@filter(ImportProduct)
class ImportProductFilter(SearchFilterMixin):
    id: auto


@filter(ImportProperty)
class ImportPropertyFilter(SearchFilterMixin):
    id: auto


@filter(ImportPropertySelectValue)
class ImportPropertySelectValueFilter(SearchFilterMixin):
    id: auto


@filter(ImportVat)
class ImportVatFilter(SearchFilterMixin):
    id: auto


@filter(RemoteCategory)
class RemoteCategoryFilter(SearchFilterMixin):
    id: auto


@filter(RemoteCustomer)
class RemoteCustomerFilter(SearchFilterMixin):
    id: auto


@filter(RemoteImage)
class RemoteImageFilter(SearchFilterMixin):
    id: auto


@filter(RemoteImageProductAssociation)
class RemoteImageProductAssociationFilter(SearchFilterMixin):
    id: auto


@filter(RemoteOrder)
class RemoteOrderFilter(SearchFilterMixin):
    id: auto


@filter(RemoteProduct)
class RemoteProductFilter(SearchFilterMixin):
    id: auto
    local_instance: Optional[lazy['ProductFilter', "products.schema.types.filters"]]

    @custom_filter
    def has_sync_requests(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ):
        if value in (None, UNSET):
            return queryset, Q()

        pending = SyncRequest.STATUS_PENDING
        pending_filter = Q(sync_requests__status=pending) | Q(sync_requests__skipped_for__status=pending)
        if value:
            return queryset.filter(pending_filter).distinct(), Q()

        return queryset.exclude(pending_filter).distinct(), Q()


@filter(RemoteProductContent)
class RemoteProductContentFilter(SearchFilterMixin):
    id: auto


@filter(RemoteProductProperty)
class RemoteProductPropertyFilter(SearchFilterMixin):
    id: auto


@filter(RemoteProperty)
class RemotePropertyFilter(SearchFilterMixin):
    id: auto
    local_instance: Optional[lazy['PropertyFilter', "properties.schema.types.filters"]]


@filter(RemoteDocumentType)
class RemoteDocumentTypeFilter:
    id: auto
    sales_channel: Optional[lazy['SalesChannelFilter', "sales_channels.schema.types.filters"]]
    local_instance: Optional[lazy['DocumentTypeFilter', "media.schema.types.filters"]]
    uploadable: auto


@filter(RemotePropertySelectValue)
class RemotePropertySelectValueFilter(SearchFilterMixin):
    id: auto


@filter(RemoteVat)
class RemoteVatFilter(SearchFilterMixin):
    id: auto


@filter(RemoteLog)
class RemoteLogFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]


@filter(SalesChannel)
class SalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto


@filter(ManualSalesChannel)
class ManualSalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto


@filter(SalesChannelIntegrationPricelist)
class SalesChannelIntegrationPricelistFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    price_list: Optional[lazy['SalesPriceListFilter', "sales_prices.schema.types.filters"]]


@filter(RemoteCurrency)
class RemoteCurrencyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]


@filter(SalesChannelImport)
class SalesChannelImportFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]


@filter(SalesChannelFeed)
class SalesChannelFeedFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    type: auto
    status: auto
    remote_id: auto


@filter(SalesChannelFeedItem)
class SalesChannelFeedItemFilter(SearchFilterMixin):
    id: auto
    feed: Optional["SalesChannelFeedFilter"]
    remote_product: Optional[RemoteProductFilter]
    sales_channel_view: Optional["SalesChannelViewFilter"]
    action: auto
    status: auto
    identifier: auto


@filter(SalesChannelView)
class SalesChannelViewFilter(SearchFilterMixin):
    search: Optional[str]
    id: auto
    remote_id: auto
    include_in_todo: auto
    todo_sort_order: auto
    sales_channel: Optional[SalesChannelFilter]


@filter(ManualSalesChannelView)
class ManualSalesChannelViewFilter(SearchFilterMixin):
    search: Optional[str]
    id: auto
    remote_id: auto
    include_in_todo: auto
    todo_sort_order: auto
    sales_channel: Optional[ManualSalesChannelFilter]


@filter(RemoteLanguage)
class RemoteLanguageFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]


@filter(SalesChannelViewAssign)
class SalesChannelViewAssignFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    sales_channel_view: Optional[SalesChannelViewFilter]
    product: Optional[ProductFilter]
    remote_product: Optional[RemoteProductFilter]

    @custom_filter
    def status(
        self,
        queryset: QuerySet,
        value: str,
        prefix: str
    ) :
        if value in (None, UNSET):
            return queryset, Q()

        return queryset.filter_by_status(status=str(value)), Q()


@filter(RejectedSalesChannelViewAssign)
class RejectedSalesChannelViewAssignFilter(SearchFilterMixin):
    id: auto
    sales_channel_view: Optional[SalesChannelViewFilter]
    product: Optional[ProductFilter]

    @custom_filter
    def has_sync_requests(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ):
        if value in (None, UNSET):
            return queryset, Q()

        pending = SyncRequest.STATUS_PENDING
        pending_filter = (
            Q(remote_product__sync_requests__status=pending)
            | Q(remote_product__sync_requests__skipped_for__status=pending)
        )
        if value:
            return queryset.filter(pending_filter).distinct(), Q()

        return queryset.exclude(pending_filter).distinct(), Q()


@filter(SalesChannelContentTemplate)
class SalesChannelContentTemplateFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    language: auto
