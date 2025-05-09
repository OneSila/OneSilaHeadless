from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyCurrency


class ShopifyRemoteCurrencyPullFactory(GetShopifyApiMixin, PullRemoteInstanceMixin):
    """
    Pulls the primary and presentment currencies configured on a Shopify store.
    """
    remote_model_class = ShopifyCurrency
    field_mapping = {
        'remote_code': 'code',
        'is_default': 'primary',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_code']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        shop = self.api.Shop.current()
        primary = shop.attributes.get('currency')
        presentment = shop.attributes.get('enabled_presentment_currencies', [])

        self.remote_instances = []
        for code in presentment:
            self.remote_instances.append({
                'code': code,
                'primary': (code == primary)
            })