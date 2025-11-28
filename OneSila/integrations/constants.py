from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.shein.models import SheinSalesChannel
from webhooks.models import WebhookIntegration

MAGENTO_INTEGRATION = 'magento'
SHOPIFY_INTEGRATION = 'shopify'
WOOCOMMERCE_INTEGRATION = 'woocommerce'
AMAZON_INTEGRATION = 'amazon'
EBAY_INTEGRATION = 'ebay'
WEBHOOK_INTEGRATION = 'webhook'
SHEIN_INTEGRATION = 'shein'

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
    (SHOPIFY_INTEGRATION, _('Shopify')),
    (WOOCOMMERCE_INTEGRATION, _('WooCommerce')),
    (AMAZON_INTEGRATION, _('Amazon')),
    (EBAY_INTEGRATION, _('Ebay')),
    (SHEIN_INTEGRATION, _('Shein')),
    (WEBHOOK_INTEGRATION, _('Webhook')),
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
    ShopifySalesChannel: SHOPIFY_INTEGRATION,
    WoocommerceSalesChannel: WOOCOMMERCE_INTEGRATION,
    AmazonSalesChannel: AMAZON_INTEGRATION,
    EbaySalesChannel: EBAY_INTEGRATION,
    SheinSalesChannel: SHEIN_INTEGRATION,
    WebhookIntegration: WEBHOOK_INTEGRATION,
}
