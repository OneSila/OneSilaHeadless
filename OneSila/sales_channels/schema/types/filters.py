from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from products.schema.types.filters import ProductFilter

from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign


@filter(ImportCurrency)
class ImportCurrencyFilter(SearchFilterMixin):
    pass


@filter(ImportImage)
class ImportImageFilter(SearchFilterMixin):
    pass


@filter(ImportProcess)
class ImportProcessFilter(SearchFilterMixin):
    pass


@filter(ImportProduct)
class ImportProductFilter(SearchFilterMixin):
    pass


@filter(ImportProperty)
class ImportPropertyFilter(SearchFilterMixin):
    pass


@filter(ImportPropertySelectValue)
class ImportPropertySelectValueFilter(SearchFilterMixin):
    pass


@filter(ImportVat)
class ImportVatFilter(SearchFilterMixin):
    pass


@filter(RemoteCategory)
class RemoteCategoryFilter(SearchFilterMixin):
    pass


@filter(RemoteCurrency)
class RemoteCurrencyFilter(SearchFilterMixin):
    pass


@filter(RemoteCustomer)
class RemoteCustomerFilter(SearchFilterMixin):
    pass


@filter(RemoteImage)
class RemoteImageFilter(SearchFilterMixin):
    pass


@filter(RemoteImageProductAssociation)
class RemoteImageProductAssociationFilter(SearchFilterMixin):
    pass


@filter(RemoteInventory)
class RemoteInventoryFilter(SearchFilterMixin):
    pass


@filter(RemoteLog)
class RemoteLogFilter(SearchFilterMixin):
    pass


@filter(RemoteOrder)
class RemoteOrderFilter(SearchFilterMixin):
    pass


@filter(RemotePrice)
class RemotePriceFilter(SearchFilterMixin):
    pass


@filter(RemoteProduct)
class RemoteProductFilter(SearchFilterMixin):
    pass


@filter(RemoteProductContent)
class RemoteProductContentFilter(SearchFilterMixin):
    pass


@filter(RemoteProductProperty)
class RemoteProductPropertyFilter(SearchFilterMixin):
    pass


@filter(RemoteProperty)
class RemotePropertyFilter(SearchFilterMixin):
    pass


@filter(RemotePropertySelectValue)
class RemotePropertySelectValueFilter(SearchFilterMixin):
    pass


@filter(RemoteVat)
class RemoteVatFilter(SearchFilterMixin):
    pass


@filter(SalesChannel)
class SalesChannelFilter(SearchFilterMixin):
    pass


@filter(SalesChannelIntegrationPricelist)
class SalesChannelIntegrationPricelistFilter(SearchFilterMixin):
    id: auto


@filter(SalesChannelView)
class SalesChannelViewFilter(SearchFilterMixin):
    id: auto


@filter(SalesChannelViewAssign)
class SalesChannelViewAssignFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    sales_channel_view: Optional[SalesChannelViewFilter]
    product: Optional[ProductFilter]

