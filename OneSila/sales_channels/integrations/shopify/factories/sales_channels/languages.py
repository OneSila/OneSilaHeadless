import json
from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyRemoteLanguage


class ShopifyRemoteLanguagePullFactory(GetShopifyApiMixin, PullRemoteInstanceMixin):
    """
    Pulls the storefront locales (languages) configured on a Shopify shop via GraphQL.
    Each locale is stored as a ShopifyRemoteLanguage mirror.
    """
    remote_model_class = ShopifyRemoteLanguage
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
        """
        Overrides the default to call GraphQL shop.locales and build a list of dicts.
        """
        gql = self.api.GraphQL()
        query = '''
            query {
              shopLocales {
                locale
                primary
                published
              }
            }
        '''

        response = gql.execute(query)
        data = json.loads(response)
        locales = data.get('data', {}).get('shopLocales', [])

        self.remote_instances = [
            {
                'code': loc.get('locale'),
            }
            for loc in locales if loc.get('locale')
        ]

    def update_get_or_create_lookup(self, lookup, remote_data):
        return lookup
