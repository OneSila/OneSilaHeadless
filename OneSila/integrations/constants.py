from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.integrations.amazon.models import AmazonSalesChannel

MAGENTO_INTEGRATION = 'magento'
SHOPIFY_INTEGRATION = 'shopify'
WOOCOMMERCE_INTEGRATION = 'woocommerce'
AMAZON_INTEGRATION = 'amazon'
EBAY_INTEGRATION = 'ebay'

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
    (SHOPIFY_INTEGRATION, _('Shopify')),
    (WOOCOMMERCE_INTEGRATION, _('WooCommerce')),
    (AMAZON_INTEGRATION, _('Amazon')),
    (EBAY_INTEGRATION, _('Ebay')),
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
    ShopifySalesChannel: SHOPIFY_INTEGRATION,
    WoocommerceSalesChannel: WOOCOMMERCE_INTEGRATION,
    AmazonSalesChannel: AMAZON_INTEGRATION,
    EbaySalesChannel: EBAY_INTEGRATION,
}
