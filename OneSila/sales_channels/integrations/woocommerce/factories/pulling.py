from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceCurrency, \
    WoocommerceRemoteLanguage
from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannelView
from sales_channels.integrations.woocommerce.exceptions import FailedToGetStoreConfigError
import logging
logger = logging.getLogger(__name__)


class WoocommerceRemoteCurrencyPullFactory(GetWoocommerceAPIMixin, PullRemoteInstanceMixin):
    """
    Pulls the primary and presentment currencies configured on a Woocommerce store.
    """
    remote_model_class = WoocommerceCurrency
    field_mapping = {
        'remote_code': 'remote_code',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_code']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        currency = self.api.get_store_currency()
        self.remote_instances = [{'remote_code': currency, }]


class WoocommerceLanguagePullFactory(GetWoocommerceAPIMixin, PullRemoteInstanceMixin):
    """
    Pulls the woocommerce locales (languages) configured.
    Each locale is stored as a WoocommerceRemoteLanguage mirror.
    """
    remote_model_class = WoocommerceRemoteLanguage
    field_mapping = {
        'remote_code': 'locale',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_code']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        """
        Overrides the default to call GraphQL shop.locales and build a list of dicts.
        """
        self.remote_instances = [{'locale': self.api.get_store_language()}]


class WoocommerceSalesChannelViewPullFactory(GetWoocommerceAPIMixin, PullRemoteInstanceMixin):
    """
    Pulls the single store "view" for Woocommerce (the storefront) and mirrors it as a SalesChannelView.
    """
    remote_model_class = WoocommerceSalesChannelView
    field_mapping = {
        # 'remote_id': 'id',
        'name': 'name',
        'url': 'url',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        """
        there is no such concept as a view in woocommerce.
        """
        try:
            store_config = self.api.get_store_config()
            name = store_config['name']
            url = store_config['url']

            self.remote_instances = [{
                # 'id':   store_id,
                'name': store_config['name'],
                'url': store_config['url'],
            }]
        except FailedToGetStoreConfigError:
            logger.warning("Failed to get store config, falling back to defaults.")
            name = 'WooCommerce'
            url = self.api.hostname

        self.remote_instances = [{
            'name': name,
            'url': url,
        }]
