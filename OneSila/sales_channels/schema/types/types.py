from core.schema.core.types.types import type, relay, List, Annotated, lazy
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from products.schema.types.types import ProductType

from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteTaskQueue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from .filters import ImportCurrencyFilter, ImportImageFilter, ImportProcessFilter, ImportProductFilter, ImportPropertyFilter, ImportPropertySelectValueFilter, ImportVatFilter, RemoteCategoryFilter, RemoteCurrencyFilter, RemoteCustomerFilter, RemoteImageFilter, RemoteImageProductAssociationFilter, RemoteInventoryFilter, RemoteLogFilter, RemoteOrderFilter, RemotePriceFilter, RemoteProductFilter, RemoteProductContentFilter, RemoteProductPropertyFilter, RemotePropertyFilter, RemotePropertySelectValueFilter, RemoteTaskQueueFilter, RemoteVatFilter, SalesChannelFilter, SalesChannelIntegrationPricelistFilter, SalesChannelViewFilter, SalesChannelViewAssignFilter
from .ordering import ImportCurrencyOrder, ImportImageOrder, ImportProcessOrder, ImportProductOrder, ImportPropertyOrder, ImportPropertySelectValueOrder, ImportVatOrder, RemoteCategoryOrder, RemoteCurrencyOrder, RemoteCustomerOrder, RemoteImageOrder, RemoteImageProductAssociationOrder, RemoteInventoryOrder, RemoteLogOrder, RemoteOrderOrder, RemotePriceOrder, RemoteProductOrder, RemoteProductContentOrder, RemoteProductPropertyOrder, RemotePropertyOrder, RemotePropertySelectValueOrder, RemoteTaskQueueOrder, RemoteVatOrder, SalesChannelOrder, SalesChannelIntegrationPricelistOrder, SalesChannelViewOrder, SalesChannelViewAssignOrder

@type(SalesChannel, filters=SalesChannelFilter, order=SalesChannelOrder, pagination=True, fields='__all__')
class SalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    pass

@type(ImportCurrency, filters=ImportCurrencyFilter, order=ImportCurrencyOrder, pagination=True, fields='__all__')
class ImportCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportImage, filters=ImportImageFilter, order=ImportImageOrder, pagination=True, fields='__all__')
class ImportImageType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportProcess, filters=ImportProcessFilter, order=ImportProcessOrder, pagination=True, fields='__all__')
class ImportProcessType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportProduct, filters=ImportProductFilter, order=ImportProductOrder, pagination=True, fields='__all__')
class ImportProductType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportProperty, filters=ImportPropertyFilter, order=ImportPropertyOrder, pagination=True, fields='__all__')
class ImportPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportPropertySelectValue, filters=ImportPropertySelectValueFilter, order=ImportPropertySelectValueOrder, pagination=True, fields='__all__')
class ImportPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(ImportVat, filters=ImportVatFilter, order=ImportVatOrder, pagination=True, fields='__all__')
class ImportVatType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteCategory, filters=RemoteCategoryFilter, order=RemoteCategoryOrder, pagination=True, fields='__all__')
class RemoteCategoryType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteCurrency, filters=RemoteCurrencyFilter, order=RemoteCurrencyOrder, pagination=True, fields='__all__')
class RemoteCurrencyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteCustomer, filters=RemoteCustomerFilter, order=RemoteCustomerOrder, pagination=True, fields='__all__')
class RemoteCustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteImage, filters=RemoteImageFilter, order=RemoteImageOrder, pagination=True, fields='__all__')
class RemoteImageType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteImageProductAssociation, filters=RemoteImageProductAssociationFilter, order=RemoteImageProductAssociationOrder, pagination=True, fields='__all__')
class RemoteImageProductAssociationType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteInventory, filters=RemoteInventoryFilter, order=RemoteInventoryOrder, pagination=True, fields='__all__')
class RemoteInventoryType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteLog, filters=RemoteLogFilter, order=RemoteLogOrder, pagination=True, fields='__all__')
class RemoteLogType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteOrder, filters=RemoteOrderFilter, order=RemoteOrderOrder, pagination=True, fields='__all__')
class RemoteOrderType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemotePrice, filters=RemotePriceFilter, order=RemotePriceOrder, pagination=True, fields='__all__')
class RemotePriceType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteProduct, filters=RemoteProductFilter, order=RemoteProductOrder, pagination=True, fields='__all__')
class RemoteProductType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteProductContent, filters=RemoteProductContentFilter, order=RemoteProductContentOrder, pagination=True, fields='__all__')
class RemoteProductContentType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteProductProperty, filters=RemoteProductPropertyFilter, order=RemoteProductPropertyOrder, pagination=True, fields='__all__')
class RemoteProductPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteProperty, filters=RemotePropertyFilter, order=RemotePropertyOrder, pagination=True, fields='__all__')
class RemotePropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemotePropertySelectValue, filters=RemotePropertySelectValueFilter, order=RemotePropertySelectValueOrder, pagination=True, fields='__all__')
class RemotePropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteTaskQueue, filters=RemoteTaskQueueFilter, order=RemoteTaskQueueOrder, pagination=True, fields='__all__')
class RemoteTaskQueueType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(RemoteVat, filters=RemoteVatFilter, order=RemoteVatOrder, pagination=True, fields='__all__')
class RemoteVatType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(SalesChannelIntegrationPricelist, filters=SalesChannelIntegrationPricelistFilter, order=SalesChannelIntegrationPricelistOrder, pagination=True, fields='__all__')
class SalesChannelIntegrationPricelistType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(SalesChannelView, filters=SalesChannelViewFilter, order=SalesChannelViewOrder, pagination=True, fields='__all__')
class SalesChannelViewType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType


@type(SalesChannelViewAssign, filters=SalesChannelViewAssignFilter, order=SalesChannelViewAssignOrder, pagination=True, fields='__all__')
class SalesChannelViewAssignType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: SalesChannelType
    sales_channel_view: SalesChannelViewType
    remote_product: RemoteProductType
    product: ProductType

