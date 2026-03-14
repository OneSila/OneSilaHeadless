from core.schema.core.types.input import NodeInput, input, partial
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)


@input(MiraklSalesChannel, exclude=["integration_ptr", "saleschannel_ptr"])
class MiraklSalesChannelInput:
    pass


@partial(MiraklSalesChannel, fields="__all__")
class MiraklSalesChannelPartialInput(NodeInput):
    pass


@input(MiraklProductCategory, exclude=["remoteproductcategory_ptr"])
class MiraklProductCategoryInput:
    pass


@partial(MiraklProductCategory, fields="__all__")
class MiraklProductCategoryPartialInput(NodeInput):
    pass


@partial(MiraklSalesChannelView, fields="__all__")
class MiraklSalesChannelViewPartialInput(NodeInput):
    pass


@partial(MiraklRemoteCurrency, fields="__all__")
class MiraklRemoteCurrencyPartialInput(NodeInput):
    pass


@partial(MiraklRemoteLanguage, fields="__all__")
class MiraklRemoteLanguagePartialInput(NodeInput):
    pass


@partial(MiraklCategory, fields="__all__")
class MiraklCategoryPartialInput(NodeInput):
    pass


@partial(MiraklDocumentType, fields="__all__")
class MiraklDocumentTypePartialInput(NodeInput):
    pass


@partial(MiraklProductType, fields="__all__")
class MiraklProductTypePartialInput(NodeInput):
    pass


@partial(MiraklProperty, fields="__all__")
class MiraklPropertyPartialInput(NodeInput):
    pass


@partial(MiraklPropertySelectValue, fields="__all__")
class MiraklPropertySelectValuePartialInput(NodeInput):
    pass


@partial(MiraklProductTypeItem, fields="__all__")
class MiraklProductTypeItemPartialInput(NodeInput):
    pass
