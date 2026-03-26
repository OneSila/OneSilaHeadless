from typing import Annotated, List, Optional

from core.schema.core.types.types import GetQuerysetMultiTenantMixin, field, lazy, relay, type
from currencies.schema.types.types import CurrencyType
from imports_exports.schema.queries import ImportType
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductIssue,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelImport,
    MiraklSalesChannelImportExportFile,
    MiraklSalesChannelView,
)
from sales_channels.integrations.mirakl.schema.types.filters import (
    MiraklCategoryFilter,
    MiraklDocumentTypeFilter,
    MiraklEanCodeFilter,
    MiraklPriceFilter,
    MiraklProductIssueFilter,
    MiraklProductCategoryFilter,
    MiraklProductContentMiraklFilter,
    MiraklProductFilter,
    MiraklProductTypeFilter,
    MiraklProductTypeItemFilter,
    MiraklPropertyFilter,
    MiraklPropertySelectValueFilter,
    MiraklRemoteCurrencyFilter,
    MiraklRemoteLanguageFilter,
    MiraklSalesChannelFilter,
    MiraklSalesChannelFeedFilter,
    MiraklSalesChannelFeedItemFilter,
    MiraklSalesChannelImportFilter,
    MiraklSalesChannelImportExportFileFilter,
    MiraklSalesChannelViewFilter,
)
from sales_channels.integrations.mirakl.schema.types.ordering import (
    MiraklCategoryOrder,
    MiraklDocumentTypeOrder,
    MiraklEanCodeOrder,
    MiraklPriceOrder,
    MiraklProductIssueOrder,
    MiraklProductCategoryOrder,
    MiraklProductContentOrder,
    MiraklProductOrder,
    MiraklProductTypeOrder,
    MiraklProductTypeItemOrder,
    MiraklPropertyOrder,
    MiraklPropertySelectValueOrder,
    MiraklRemoteCurrencyOrder,
    MiraklRemoteLanguageOrder,
    MiraklSalesChannelImportOrder,
    MiraklSalesChannelImportExportFileOrder,
    MiraklSalesChannelFeedItemOrder,
    MiraklSalesChannelFeedOrder,
    MiraklSalesChannelOrder,
    MiraklSalesChannelViewOrder,
)
from strawberry.relay import to_base64


@type(
    MiraklSalesChannel,
    filters=MiraklSalesChannelFilter,
    order=MiraklSalesChannelOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    feed_batches: List[Annotated["SalesChannelFeedType", lazy("sales_channels.schema.types.types")]]

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr

    @field()
    def connected(self, info) -> bool:
        instance = self.get_real_instance() if hasattr(self, "get_real_instance") else self
        return instance.connected


@type(
    MiraklSalesChannelView,
    filters=MiraklSalesChannelViewFilter,
    order=MiraklSalesChannelViewOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]

    @field()
    def active(self, info) -> Optional[bool]:
        return getattr(self.sales_channel, "active", None)


@type(
    MiraklRemoteCurrency,
    filters=MiraklRemoteCurrencyFilter,
    order=MiraklRemoteCurrencyOrder,
    pagination=True,
    fields="__all__",
)
class MiraklRemoteCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[CurrencyType]


@type(
    MiraklRemoteLanguage,
    filters=MiraklRemoteLanguageFilter,
    order=MiraklRemoteLanguageOrder,
    pagination=True,
    fields="__all__",
)
class MiraklRemoteLanguageType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklCategory,
    filters=MiraklCategoryFilter,
    order=MiraklCategoryOrder,
    pagination=True,
    fields="__all__",
)
class MiraklCategoryType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    parent: Optional[Annotated["MiraklCategoryType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    children: List[Annotated["MiraklCategoryType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    product_types: List[Annotated["MiraklProductTypeType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]


@type(
    MiraklDocumentType,
    filters=MiraklDocumentTypeFilter,
    order=MiraklDocumentTypeOrder,
    pagination=True,
    fields="__all__",
)
class MiraklDocumentTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["DocumentTypeType", lazy("media.schema.types.types")]]


@type(
    MiraklProperty,
    filters=MiraklPropertyFilter,
    order=MiraklPropertyOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["PropertyType", lazy("properties.schema.types.types")]]

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            return bool(getattr(self, "remote_id", None))
        return annotated_value


@type(
    MiraklPropertySelectValue,
    filters=MiraklPropertySelectValueFilter,
    order=MiraklPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
    disable_optimization=True,
)
class MiraklPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    remote_property: Annotated["MiraklPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["PropertySelectValueType", lazy("properties.schema.types.types")]]

    @field()
    def label(self, info) -> str:
        return self.value or self.code

    @field()
    def mapped_locally(self, info) -> bool:
        annotated_value = getattr(self, "mapped_locally", None)
        if annotated_value is None:
            return bool(getattr(self, "local_instance_id", None))
        return annotated_value

    @field()
    def mapped_remotely(self, info) -> bool:
        annotated_value = getattr(self, "mapped_remotely", None)
        if annotated_value is None:
            return bool(getattr(self, "remote_id", None))
        return annotated_value


@type(
    MiraklProductType,
    filters=MiraklProductTypeFilter,
    order=MiraklProductTypeOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    category: Optional[Annotated["MiraklCategoryType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    local_instance: Optional[Annotated["ProductPropertiesRuleType", lazy("properties.schema.types.types")]]
    items: List[Annotated["MiraklProductTypeItemType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]

    @field()
    def mapped_locally(self, info) -> bool:
        return bool(getattr(self, "local_instance_id", None))

    @field()
    def mapped_remotely(self, info) -> bool:
        return bool(getattr(self, "remote_id", None))

    @field()
    def ready_to_push(self, info) -> bool:
        return bool(getattr(self, "ready_to_push", False))

    @field()
    def template_url(self, info) -> str | None:
        return getattr(self, "template_url", None)


@type(
    MiraklProductTypeItem,
    filters=MiraklProductTypeItemFilter,
    order=MiraklProductTypeItemOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductTypeItemType(relay.Node, GetQuerysetMultiTenantMixin):
    product_type: Annotated["MiraklProductTypeType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    remote_property: Annotated["MiraklPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["ProductPropertiesRuleItemType", lazy("properties.schema.types.types")]]


@type(
    MiraklProductCategory,
    filters=MiraklProductCategoryFilter,
    order=MiraklProductCategoryOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductCategoryType(relay.Node, GetQuerysetMultiTenantMixin):
    product: Annotated["ProductType", lazy("products.schema.types.types")]
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklProduct,
    filters=MiraklProductFilter,
    order=MiraklProductOrder,
    pagination=True,
    fields="__all__",
)
class MiraklRemoteProductType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["ProductType", lazy("products.schema.types.types")]]
    remote_parent_product: Optional[Annotated["RemoteProductType", lazy("sales_channels.schema.types.types")]]


@type(
    MiraklProductIssue,
    filters=MiraklProductIssueFilter,
    order=MiraklProductIssueOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductIssueType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklRemoteProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    views: List[Annotated["MiraklSalesChannelViewType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]


@type(
    MiraklSalesChannelFeed,
    filters=MiraklSalesChannelFeedFilter,
    order=MiraklSalesChannelFeedOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelFeedType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    product_type: Optional[Annotated["MiraklProductTypeType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    sales_channel_view: Optional[Annotated["MiraklSalesChannelViewType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    items: List[Annotated["MiraklSalesChannelFeedItemType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]
    products: List[Annotated["ProductType", lazy("products.schema.types.types")]]

    @field()
    def file_url(self, info) -> Optional[str]:
        return MiraklSalesChannelFeed.file_url.fget(self)

    @field()
    def error_report_file_url(self, info) -> Optional[str]:
        return MiraklSalesChannelFeed.error_report_file_url.fget(self)

    @field()
    def new_product_report_file_url(self, info) -> Optional[str]:
        return MiraklSalesChannelFeed.new_product_report_file_url.fget(self)

    @field()
    def transformed_file_url(self, info) -> Optional[str]:
        return MiraklSalesChannelFeed.transformed_file_url.fget(self)

    @field()
    def transformation_error_report_file_url(self, info) -> Optional[str]:
        return MiraklSalesChannelFeed.transformation_error_report_file_url.fget(self)

    @field()
    def products(self, info) -> List[Annotated["ProductType", lazy("products.schema.types.types")]]:
        from products.models import Product
        ids = MiraklSalesChannelFeedItem.objects.filter(feed=self).values_list('remote_product__local_instance_id', flat=True)

        return list(
            Product.objects.filter(
                id__in=ids,
            )
            .distinct()
            .order_by("id")
        )


@type(
    MiraklSalesChannelFeedItem,
    filters=MiraklSalesChannelFeedItemFilter,
    order=MiraklSalesChannelFeedItemOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelFeedItemType(relay.Node, GetQuerysetMultiTenantMixin):
    feed: Annotated["MiraklSalesChannelFeedType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    remote_product: Annotated["MiraklRemoteProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    sales_channel_view: Optional[Annotated["MiraklSalesChannelViewType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]


@type(
    MiraklProductContent,
    filters=MiraklProductContentMiraklFilter,
    order=MiraklProductContentOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductContentType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklRemoteProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklPrice,
    filters=MiraklPriceFilter,
    order=MiraklPriceOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPriceType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklRemoteProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklEanCode,
    filters=MiraklEanCodeFilter,
    order=MiraklEanCodeOrder,
    pagination=True,
    fields="__all__",
)
class MiraklEanCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklRemoteProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklSalesChannelImport,
    filters=MiraklSalesChannelImportFilter,
    order=MiraklSalesChannelImportOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelImportType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    export_files: List[Annotated["MiraklSalesChannelImportExportFileType", lazy("sales_channels.integrations.mirakl.schema.types.types")]]

    @field()
    def import_id(self, info) -> str:
        return to_base64(ImportType, self.pk)

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.schema.types.types import SalesChannelImportType

        return to_base64(SalesChannelImportType, self.pk)


@type(
    MiraklSalesChannelImportExportFile,
    filters=MiraklSalesChannelImportExportFileFilter,
    order=MiraklSalesChannelImportExportFileOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelImportExportFileType(relay.Node, GetQuerysetMultiTenantMixin):
    import_process: Annotated["MiraklSalesChannelImportType", lazy("sales_channels.integrations.mirakl.schema.types.types")]

    @field()
    def file_url(self, info) -> Optional[str]:
        return getattr(self, "file_url", None)
