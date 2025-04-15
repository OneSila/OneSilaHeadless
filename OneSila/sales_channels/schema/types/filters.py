from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from products.schema.types.filters import ProductFilter

from sales_channels.models import ImportCurrency, ImportImage, SalesChannelImport, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from sales_channels.models.sales_channels import RemoteLanguage


@filter(ImportCurrency)
class ImportCurrencyFilter(SearchFilterMixin):
    pass


@filter(ImportImage)
class ImportImageFilter(SearchFilterMixin):
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


@filter(RemoteOrder)
class RemoteOrderFilter(SearchFilterMixin):
    pass

@filter(RemoteProduct)
class RemoteProductFilter(SearchFilterMixin):
    id: auto


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


@filter(RemoteLog)
class RemoteLogFilter(SearchFilterMixin):
    id: auto
    remote_product: Optional[RemoteProductFilter]



@filter(SalesChannel)
class SalesChannelFilter(SearchFilterMixin):
    id: auto
    active: auto


@filter(SalesChannelIntegrationPricelist)
class SalesChannelIntegrationPricelistFilter(SearchFilterMixin):
    id: auto

@filter(RemoteCurrency)
class RemoteCurrencyFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]

@filter(SalesChannelImport)
class SalesChannelImportFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]

@filter(SalesChannelView)
class SalesChannelViewFilter(SearchFilterMixin):
    id: auto
    sales_channel: Optional[SalesChannelFilter]

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

