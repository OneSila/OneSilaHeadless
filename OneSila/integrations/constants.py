from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.amazon.models import AmazonSalesChannel

MAGENTO_INTEGRATION = 'magento'
SHOPIFY_INTEGRATION = 'shopify'
AMAZON_INTEGRATION = 'amazon'

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
    (SHOPIFY_INTEGRATION, _('Shopify')),
    (AMAZON_INTEGRATION, _('Amazon')),
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
    ShopifySalesChannel: SHOPIFY_INTEGRATION,
    AmazonSalesChannel: AMAZON_INTEGRATION,
}
