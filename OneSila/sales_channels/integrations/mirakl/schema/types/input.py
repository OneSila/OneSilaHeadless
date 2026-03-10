from core.schema.core.types.input import NodeInput, input, partial
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
    MiraklProductCategory,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
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


@partial(MiraklInternalProperty, fields="__all__")
class MiraklInternalPropertyPartialInput(NodeInput):
    pass


@partial(MiraklInternalPropertyOption, fields="__all__")
class MiraklInternalPropertyOptionPartialInput(NodeInput):
    pass


@partial(MiraklCategory, fields="__all__")
class MiraklCategoryPartialInput(NodeInput):
    pass


@partial(MiraklProperty, fields="__all__")
class MiraklPropertyPartialInput(NodeInput):
    pass


@partial(MiraklPropertySelectValue, fields="__all__")
class MiraklPropertySelectValuePartialInput(NodeInput):
    pass


@partial(MiraklPropertyApplicability, fields="__all__")
class MiraklPropertyApplicabilityPartialInput(NodeInput):
    pass


@partial(MiraklProductTypeItem, fields="__all__")
class MiraklProductTypeItemPartialInput(NodeInput):
    pass


@partial(MiraklDocumentType, fields="__all__")
class MiraklDocumentTypePartialInput(NodeInput):
    pass
