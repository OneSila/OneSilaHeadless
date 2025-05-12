from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from sales_channels.integrations.shopify.models import ShopifySalesChannel


@filter(ShopifySalesChannel)
class ShopifySalesChannelFilter(SearchFilterMixin):
    active: auto