from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifySalesChannelView


class ShopifySalesChannelViewPullFactory(GetShopifyApiMixin, PullRemoteInstanceMixin):
    """
    Pulls the single store "view" for Shopify (the storefront) and mirrors it as a SalesChannelView.
    """
    remote_model_class = ShopifySalesChannelView
    field_mapping = {
        'remote_id': 'id',
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
        Override to fetch the single shop as the one view.
        """
        self.set_api()
        shop = self.api.Shop.current()
        domain = getattr(shop, 'domain', None) or getattr(shop, 'myshopify_domain', None)
        url = f"https://{domain}" if domain else ''
        self.remote_instances = [{
            'id':   shop.id,
            'name': shop.name,
            'url':  url,
        }]

    def serialize_response(self, response):
        return response