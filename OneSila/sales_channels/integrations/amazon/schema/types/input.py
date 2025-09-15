from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProduct,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonSalesChannelImport,
    AmazonDefaultUnitConfigurator,
    AmazonSalesChannelView,
    AmazonProductBrowseNode,
    AmazonExternalProductId,
    AmazonGtinExemption,
    AmazonVariationTheme,
)
from properties.schema.types.input import PropertySelectValuePartialInput
from strawberry.relay import GlobalID
from typing import List, Optional


@input(AmazonSalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class AmazonSalesChannelInput:
    pass


@partial(AmazonSalesChannel, fields="__all__")
class AmazonSalesChannelPartialInput(NodeInput):
    pass


@input(AmazonProperty, fields="__all__")
class AmazonPropertyInput:
    pass


@partial(AmazonProperty, fields="__all__")
class AmazonPropertyPartialInput(NodeInput):
    pass


@input(AmazonPropertySelectValue, fields="__all__")
class AmazonPropertySelectValueInput:
    pass


@partial(AmazonPropertySelectValue, fields="__all__")
class AmazonPropertySelectValuePartialInput(NodeInput):
    pass


@strawberry_input
class AmazonValidateAuthInput:
    spapi_oauth_code: str
    selling_partner_id: str
    state: str


@input(AmazonProductType, fields="__all__")
class AmazonProductTypeInput:
    pass


@partial(AmazonProductType, fields="__all__")
class AmazonProductTypePartialInput(NodeInput):
    pass


@input(AmazonProductTypeItem, fields="__all__")
class AmazonProductTypeItemInput:
    pass


@partial(AmazonProductTypeItem, fields="__all__")
class AmazonProductTypeItemPartialInput(NodeInput):
    pass


@input(AmazonProduct, fields="__all__")
class AmazonProductInput:
    pass


@partial(AmazonProduct, fields="__all__")
class AmazonProductPartialInput(NodeInput):
    pass


@input(AmazonSalesChannelImport, exclude=['saleschannelimport_ptr', 'import_ptr'])
class AmazonSalesChannelImportInput:
    pass


@partial(AmazonSalesChannelImport, fields="__all__")
class AmazonSalesChannelImportPartialInput(NodeInput):
    pass


@input(AmazonDefaultUnitConfigurator, fields="__all__")
class AmazonDefaultUnitConfiguratorInput:
    pass


@partial(AmazonDefaultUnitConfigurator, fields="__all__")
class AmazonDefaultUnitConfiguratorPartialInput(NodeInput):
    pass


@input(AmazonSalesChannelView, fields="__all__")
class AmazonSalesChannelViewInput:
    pass


@partial(AmazonSalesChannelView, fields="__all__")
class AmazonSalesChannelViewPartialInput(NodeInput):
    pass


@strawberry_input
class BulkAmazonPropertySelectValueLocalInstanceInput:
    ids: List[GlobalID]
    local_instance_id: Optional[GlobalID] = None


@input(AmazonProductBrowseNode, fields="__all__")
class AmazonProductBrowseNodeInput:
    pass


@partial(AmazonProductBrowseNode, fields="__all__")
class AmazonProductBrowseNodePartialInput(NodeInput):
    pass


@input(AmazonExternalProductId, fields="__all__")
class AmazonExternalProductIdInput:
    pass


@partial(AmazonExternalProductId, fields="__all__")
class AmazonExternalProductIdPartialInput(NodeInput):
    pass


@input(AmazonGtinExemption, fields="__all__")
class AmazonGtinExemptionInput:
    pass


@partial(AmazonGtinExemption, fields="__all__")
class AmazonGtinExemptionPartialInput(NodeInput):
    pass


@input(AmazonVariationTheme, fields="__all__")
class AmazonVariationThemeInput:
    pass


@partial(AmazonVariationTheme, fields="__all__")
class AmazonVariationThemePartialInput(NodeInput):
    pass
