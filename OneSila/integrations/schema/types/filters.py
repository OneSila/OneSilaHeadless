
from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from integrations.models import Integration, PublicIntegrationType, PublicIssue, PublicIssueCategory


@filter(Integration)
class IntegrationFilter(SearchFilterMixin):
    id: auto
    hostname: auto
    active: auto
    verify_ssl: auto


@filter(PublicIntegrationType)
class PublicIntegrationTypeFilter(SearchFilterMixin):
    id: auto
    key: auto
    type: auto
    subtype: auto
    category: auto
    active: auto
    is_beta: auto
    supports_open_ai_product_feed: auto
    sort_order: auto
    based_to: Optional["PublicIntegrationTypeFilter"]


@filter(PublicIssueCategory)
class PublicIssueCategoryFilter(SearchFilterMixin):
    id: auto
    name: auto
    code: auto


@filter(PublicIssue)
class PublicIssueFilter(SearchFilterMixin):
    id: auto
    code: auto
    recommended_fix: auto
    integration_type: Optional[PublicIntegrationTypeFilter]
    categories: Optional[PublicIssueCategoryFilter]