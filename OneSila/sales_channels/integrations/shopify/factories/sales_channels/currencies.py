import json

from sales_channels.factories.mixins import PullRemoteInstanceMixin, LocalCurrencyMappingMixin
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyCurrency


class ShopifyRemoteCurrencyPullFactory(GetShopifyApiMixin, LocalCurrencyMappingMixin, PullRemoteInstanceMixin):
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
        gql = self.api.GraphQL()
        query = """
        {
          shop {
            currencyCode
          }
        }
        """
        response = gql.execute(query)
        data = json.loads(response)
        shop_data = data["data"]["shop"]

        primary = shop_data["currencyCode"]

        self.remote_instances = [{
            'code': primary,
            'primary': True,
        }]
        self.add_local_currency()

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        super().create_remote_instance_mirror(remote_data, remote_instance_mirror)
        currency = remote_data.get('local_currency')
        if currency and not remote_instance_mirror.local_instance:
            remote_instance_mirror.local_instance = currency
            remote_instance_mirror.save(update_fields=['local_instance'])
