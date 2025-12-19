"""Ordering definitions for Shein GraphQL types."""

from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductCategory,
    SheinProductIssue,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteCurrency,
    SheinSalesChannel,
    SheinSalesChannelView,
    SheinSalesChannelImport,
)


@order(SheinSalesChannel)
class SheinSalesChannelOrder:
    id: auto


@order(SheinSalesChannelView)
class SheinSalesChannelViewOrder:
    id: auto


@order(SheinSalesChannelImport)
class SheinSalesChannelImportOrder:
    id: auto


@order(SheinRemoteCurrency)
class SheinRemoteCurrencyOrder:
    id: auto


@order(SheinProperty)
class SheinPropertyOrder:
    id: auto
    name: auto


@order(SheinPropertySelectValue)
class SheinPropertySelectValueOrder:
    id: auto
    value: auto


@order(SheinProductType)
class SheinProductTypeOrder:
    id: auto
    name: auto


@order(SheinProductTypeItem)
class SheinProductTypeItemOrder:
    id: auto


@order(SheinInternalProperty)
class SheinInternalPropertyOrder:
    id: auto
    code: auto


@order(SheinInternalPropertyOption)
class SheinInternalPropertyOptionOrder:
    id: auto
    label: auto


@order(SheinCategory)
class SheinCategoryOrder:
    id: auto
    name: auto


@order(SheinProductCategory)
class SheinProductCategoryOrder:
    id: auto
    remote_id: auto
    site_remote_id: auto


@order(SheinProductIssue)
class SheinProductIssueOrder:
    id: auto
    spu_name: auto
    skc_name: auto
    version: auto
    document_sn: auto
    document_state: auto
    audit_state: auto
    is_active: auto
