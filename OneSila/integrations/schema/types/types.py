from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field
from integrations.models import Integration
from integrations.schema.types.filters import IntegrationFilter
from integrations.schema.types.ordering import IntegrationOrder
from integrations.constants import INTEGRATIONS_TYPES_MAP, MAGENTO_INTEGRATION
from strawberry.relay.utils import to_base64


@type(Integration, filters=IntegrationFilter, order=IntegrationOrder, pagination=True, fields="__all__")
class IntegrationType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def type(self, info) -> str:
        return INTEGRATIONS_TYPES_MAP.get(self.__class__, MAGENTO_INTEGRATION)

    @field()
    def connected(self, info) -> bool:
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.amazon.models import AmazonSalesChannel

        if isinstance(self, MagentoSalesChannel):
            return True
        elif isinstance(self, ShopifySalesChannel):
            return self.access_token is not None
        elif isinstance(self, WoocommerceSalesChannel):
            return bool(self.api_key and self.api_secret)
        elif isinstance(self, AmazonSalesChannel):
            return self.access_token is not None

        raise NotImplementedError(f"Integration type {self.__class__} not implemented")

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.magento2.schema.types.types import MagentoSalesChannelType
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.woocommerce.schema.types.types import WoocommerceSalesChannelType
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.amazon.schema.types.types import AmazonSalesChannelType

        if isinstance(self, MagentoSalesChannel):
            graphql_type = MagentoSalesChannelType
        elif isinstance(self, ShopifySalesChannel):
            graphql_type = ShopifySalesChannelType
        elif isinstance(self, WoocommerceSalesChannel):
            graphql_type = WoocommerceSalesChannelType
        elif isinstance(self, AmazonSalesChannel):
            graphql_type = AmazonSalesChannelType
        else:
            raise NotImplementedError(f"Integration type {self.__class__} not implemented")

        return to_base64(graphql_type, self.pk)
