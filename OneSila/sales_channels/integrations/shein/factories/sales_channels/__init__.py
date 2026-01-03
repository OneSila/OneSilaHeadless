"""Factories handling Shein sales-channel setup operations."""

from .categories import SheinCategorySuggestionFactory
from .full_schema import SheinCategoryTreeSyncFactory
from .marketplaces import SheinMarketplacePullFactory
from .oauth import GetSheinRedirectUrlFactory, ValidateSheinAuthFactory
from .views import SheinSalesChannelViewPullFactory
from .issues import FetchRemoteIssuesFactory

__all__ = [
    "SheinCategorySuggestionFactory",
    "SheinCategoryTreeSyncFactory",
    "GetSheinRedirectUrlFactory",
    "SheinMarketplacePullFactory",
    "SheinSalesChannelViewPullFactory",
    "FetchRemoteIssuesFactory",
    "ValidateSheinAuthFactory",
]
