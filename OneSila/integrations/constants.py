from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.shopify.models import ShopifySalesChannel

MAGENTO_INTEGRATION = 'magento'
SHOPIFY_INTEGRATION = 'shopify'

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
    (SHOPIFY_INTEGRATION, _('Shopify')),
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
    ShopifySalesChannel: SHOPIFY_INTEGRATION,
}
