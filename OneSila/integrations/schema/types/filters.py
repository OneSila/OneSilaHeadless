
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from integrations.models import Integration


@filter(Integration)
class IntegrationFilter(SearchFilterMixin):
    id: auto
    hostname: auto
    active: auto
    verify_ssl: auto