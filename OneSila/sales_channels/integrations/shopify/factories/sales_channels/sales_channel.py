from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin


class TryConnection(GetShopifyApiMixin):
    """
    Validates that the stored credentials on the ShopifySalesChannel can successfully
    connect to the target store by fetching the Shop resource.
    """
    def __init__(self, sales_channel, **kwargs):

        self.sales_channel = sales_channel
        try:
            self.set_api()
            shop = self.api.Shop.current()
        except Exception as e:
            raise ConnectionError(f"Could not connect to Shopify store '{self.sales_channel.shop_url}': {e}")