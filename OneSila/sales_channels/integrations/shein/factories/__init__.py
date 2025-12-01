"""Factories and mixins for orchestrating Shein integration work."""

from .mixins import SheinSignatureMixin
from .sales_channels import SheinCategorySuggestionFactory
from .sales_channels.oauth import GetSheinRedirectUrlFactory, ValidateSheinAuthFactory
from .imports import SheinSchemaImportProcessor
from .sync import SheinSalesChannelMappingSyncFactory
from .prices import SheinPriceUpdateFactory
from .properties import (
    SheinProductPropertyCreateFactory,
    SheinProductPropertyDeleteFactory,
    SheinProductPropertyUpdateFactory,
)
from .products import (
    SheinMediaProductThroughCreateFactory,
    SheinMediaProductThroughUpdateFactory,
    SheinMediaProductThroughDeleteFactory,
    SheinProductCreateFactory,
    SheinProductUpdateFactory,
)

__all__ = [
    "SheinSignatureMixin",
    "GetSheinRedirectUrlFactory",
    "SheinCategorySuggestionFactory",
    "ValidateSheinAuthFactory",
    "SheinSchemaImportProcessor",
    "SheinSalesChannelMappingSyncFactory",
    "SheinProductPropertyCreateFactory",
    "SheinProductPropertyUpdateFactory",
    "SheinProductPropertyDeleteFactory",
    "SheinPriceUpdateFactory",
    "SheinMediaProductThroughCreateFactory",
    "SheinMediaProductThroughUpdateFactory",
    "SheinMediaProductThroughDeleteFactory",
    "SheinProductCreateFactory",
    "SheinProductUpdateFactory",
]
