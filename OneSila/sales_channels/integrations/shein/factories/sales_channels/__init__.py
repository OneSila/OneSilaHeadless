"""Factories handling Shein sales-channel setup operations."""

from .categories import SheinCategorySuggestionFactory
from .document_types import SheinCertificateRuleSyncFactory
from .document_type_translations import SheinDocumentTypeTranslationFactory
from .full_schema import SheinCategoryTreeSyncFactory
from .marketplaces import SheinMarketplacePullFactory
from .oauth import GetSheinRedirectUrlFactory, ValidateSheinAuthFactory
from .views import SheinSalesChannelViewPullFactory
from .issues import FetchRemoteIssuesFactory

__all__ = [
    "SheinCategorySuggestionFactory",
    "SheinCertificateRuleSyncFactory",
    "SheinDocumentTypeTranslationFactory",
    "SheinCategoryTreeSyncFactory",
    "GetSheinRedirectUrlFactory",
    "SheinMarketplacePullFactory",
    "SheinSalesChannelViewPullFactory",
    "FetchRemoteIssuesFactory",
    "ValidateSheinAuthFactory",
]
