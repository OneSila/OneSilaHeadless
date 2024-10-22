from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from products.schema.types.filters import ProductFilter

from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign


@filter(ImportCurrency)
class ImportCurrencyFilter(SearchFilterMixin):
    search: str | None


@filter(ImportImage)
class ImportImageFilter(SearchFilterMixin):
    search: str | None


@filter(ImportProcess)
class ImportProcessFilter(SearchFilterMixin):
    search: str | None


@filter(ImportProduct)
class ImportProductFilter(SearchFilterMixin):
    search: str | None


@filter(ImportProperty)
class ImportPropertyFilter(SearchFilterMixin):
    search: str | None


@filter(ImportPropertySelectValue)
class ImportPropertySelectValueFilter(SearchFilterMixin):
    search: str | None


@filter(ImportVat)
class ImportVatFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteCategory)
class RemoteCategoryFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteCurrency)
class RemoteCurrencyFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteCustomer)
class RemoteCustomerFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteImage)
class RemoteImageFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteImageProductAssociation)
class RemoteImageProductAssociationFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteInventory)
class RemoteInventoryFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteLog)
class RemoteLogFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteOrder)
class RemoteOrderFilter(SearchFilterMixin):
    search: str | None


@filter(RemotePrice)
class RemotePriceFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteProduct)
class RemoteProductFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteProductContent)
class RemoteProductContentFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteProductProperty)
class RemoteProductPropertyFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteProperty)
class RemotePropertyFilter(SearchFilterMixin):
    search: str | None


@filter(RemotePropertySelectValue)
class RemotePropertySelectValueFilter(SearchFilterMixin):
    search: str | None


@filter(RemoteVat)
class RemoteVatFilter(SearchFilterMixin):
    search: str | None


@filter(SalesChannel)
class SalesChannelFilter(SearchFilterMixin):
    search: str | None


@filter(SalesChannelIntegrationPricelist)
class SalesChannelIntegrationPricelistFilter(SearchFilterMixin):
    search: str | None
    id: auto


@filter(SalesChannelView)
class SalesChannelViewFilter(SearchFilterMixin):
    search: str | None
    id: auto


@filter(SalesChannelViewAssign)
class SalesChannelViewAssignFilter(SearchFilterMixin):
    search: str | None
    id: auto
    sales_channel: Optional[SalesChannelFilter]
    sales_channel_view: Optional[SalesChannelViewFilter]
    product: Optional[ProductFilter]

