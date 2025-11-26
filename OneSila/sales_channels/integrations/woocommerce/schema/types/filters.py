from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


@filter(WoocommerceSalesChannel)
class WoocommerceSalesChannelFilter(SearchFilterMixin):
    active: auto
    hostname: auto
