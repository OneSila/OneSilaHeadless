from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceCurrency

import logging
logger = logging.getLogger(__name__)


class WoocommerceRemoteCurrencyPullFactory(GetWoocommerceAPIMixin, PullRemoteInstanceMixin):
    """
    Pulls the primary and presentment currencies configured on a Woocommerce store.
    """
    remote_model_class = WoocommerceCurrency
    field_mapping = {
        'remote_code': 'code',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_code']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        currency = self.api.get_store_currency()
        self.remote_instances = [{'code': currency, }]
