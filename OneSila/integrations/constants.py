from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.magento2.models import MagentoSalesChannel

MAGENTO_INTEGRATION = 'magento'

INTEGRATIONS_TYPES = (
    (MAGENTO_INTEGRATION, _('Magento')),
)

INTEGRATIONS_TYPES_MAP = {
    MagentoSalesChannel: MAGENTO_INTEGRATION,
}