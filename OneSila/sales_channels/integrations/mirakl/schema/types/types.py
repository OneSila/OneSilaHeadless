from typing import Annotated, List, Optional

from core.schema.core.types.types import GetQuerysetMultiTenantMixin, field, lazy, relay, type
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklEanCode,
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.integrations.mirakl.schema.types.filters import (
    MiraklCategoryFilter,
    MiraklDocumentTypeFilter,
    MiraklEanCodeFilter,
    MiraklInternalPropertyFilter,
    MiraklInternalPropertyOptionFilter,
    MiraklPriceFilter,
    MiraklProductCategoryFilter,
    MiraklProductContentMiraklFilter,
    MiraklProductFilter,
    MiraklProductTypeItemFilter,
    MiraklPropertyApplicabilityFilter,
    MiraklPropertyFilter,
    MiraklPropertySelectValueFilter,
    MiraklRemoteCurrencyFilter,
    MiraklRemoteLanguageFilter,
    MiraklSalesChannelFilter,
    MiraklSalesChannelImportFilter,
    MiraklSalesChannelViewFilter,
)
from sales_channels.integrations.mirakl.schema.types.ordering import (
    MiraklCategoryOrder,
    MiraklDocumentTypeOrder,
    MiraklEanCodeOrder,
    MiraklInternalPropertyOptionOrder,
    MiraklInternalPropertyOrder,
    MiraklPriceOrder,
    MiraklProductCategoryOrder,
    MiraklProductContentOrder,
    MiraklProductOrder,
    MiraklProductTypeItemOrder,
    MiraklPropertyApplicabilityOrder,
    MiraklPropertyOrder,
    MiraklPropertySelectValueOrder,
    MiraklRemoteCurrencyOrder,
    MiraklRemoteLanguageOrder,
    MiraklSalesChannelImportOrder,
    MiraklSalesChannelOrder,
    MiraklSalesChannelViewOrder,
)


@type(
    MiraklSalesChannel,
    filters=MiraklSalesChannelFilter,
    order=MiraklSalesChannelOrder,
    pagination=True,
    exclude=["api_key"],
)
class MiraklSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr


@type(
    MiraklSalesChannelView,
    filters=MiraklSalesChannelViewFilter,
    order=MiraklSalesChannelViewOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklRemoteCurrency,
    filters=MiraklRemoteCurrencyFilter,
    order=MiraklRemoteCurrencyOrder,
    pagination=True,
    fields="__all__",
)
class MiraklRemoteCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


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
    MiraklInternalProperty,
    filters=MiraklInternalPropertyFilter,
    order=MiraklInternalPropertyOrder,
    pagination=True,
    fields="__all__",
)
class MiraklInternalPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklInternalPropertyOption,
    filters=MiraklInternalPropertyOptionFilter,
    order=MiraklInternalPropertyOptionOrder,
    pagination=True,
    fields="__all__",
)
class MiraklInternalPropertyOptionType(relay.Node, GetQuerysetMultiTenantMixin):
    internal_property: Annotated["MiraklInternalPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
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


@type(
    MiraklProperty,
    filters=MiraklPropertyFilter,
    order=MiraklPropertyOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklPropertySelectValue,
    filters=MiraklPropertySelectValueFilter,
    order=MiraklPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    remote_property: Annotated["MiraklPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklPropertyApplicability,
    filters=MiraklPropertyApplicabilityFilter,
    order=MiraklPropertyApplicabilityOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPropertyApplicabilityType(relay.Node, GetQuerysetMultiTenantMixin):
    property: Annotated["MiraklPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    view: Annotated["MiraklSalesChannelViewType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklProductTypeItem,
    filters=MiraklProductTypeItemFilter,
    order=MiraklProductTypeItemOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductTypeItemType(relay.Node, GetQuerysetMultiTenantMixin):
    category: Annotated["MiraklCategoryType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    property: Annotated["MiraklPropertyType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


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
class MiraklProductType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
    local_instance: Optional[Annotated["ProductType", lazy("products.schema.types.types")]]
    remote_parent_product: Optional[Annotated["RemoteProductType", lazy("sales_channels.schema.types.types")]]


@type(
    MiraklProductContent,
    filters=MiraklProductContentMiraklFilter,
    order=MiraklProductContentOrder,
    pagination=True,
    fields="__all__",
)
class MiraklProductContentType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklPrice,
    filters=MiraklPriceFilter,
    order=MiraklPriceOrder,
    pagination=True,
    fields="__all__",
)
class MiraklPriceType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklEanCode,
    filters=MiraklEanCodeFilter,
    order=MiraklEanCodeOrder,
    pagination=True,
    fields="__all__",
)
class MiraklEanCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    remote_product: Annotated["MiraklProductType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklDocumentType,
    filters=MiraklDocumentTypeFilter,
    order=MiraklDocumentTypeOrder,
    pagination=True,
    fields="__all__",
)
class MiraklDocumentTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]


@type(
    MiraklSalesChannelImport,
    filters=MiraklSalesChannelImportFilter,
    order=MiraklSalesChannelImportOrder,
    pagination=True,
    fields="__all__",
)
class MiraklSalesChannelImportType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Annotated["MiraklSalesChannelType", lazy("sales_channels.integrations.mirakl.schema.types.types")]
