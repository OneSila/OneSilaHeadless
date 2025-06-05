from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel

MAGENTO_INTEGRATION = 'magento'
SHOPIFY_INTEGRATION = 'shopify'
WOOCOMMERCE_INTEGRATION = 'woocommerce'  # Add this line

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
    (SHOPIFY_INTEGRATION, _('Shopify')),
    (WOOCOMMERCE_INTEGRATION, _('WooCommerce')),  # Add this line
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
    ShopifySalesChannel: SHOPIFY_INTEGRATION,
    WoocommerceSalesChannel: WOOCOMMERCE_INTEGRATION,  # Add this line
}
