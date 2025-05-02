import json
import shopify


class GetShopifyApiMixin:
    """
    Mixin to initialize and activate a Shopify session using the shop_url,
    api_version, and access_token stored on the ShopifySalesChannel.
    Also provides a method to clear the session.
    """

    def set_api(self):
        # Configure your app credentials (once per process)
        shopify.Session.setup(
            api_key=settings.SHOPIFY_API_KEY,
            secret=settings.SHOPIFY_API_SECRET,
        )

        # Create and activate a session for the specific shop
        session = shopify.Session(
            self.sales_channel.shop_url,
            self.sales_channel.api_version,
            self.sales_channel.access_token,
        )
        shopify.ShopifyResource.activate_session(session)
        self.api = shopify

    def clear_api(self):
        """
        Terminates the current Shopify session, clearing out any activated credentials.
        """
        shopify.ShopifyResource.clear_session()
        self.api = None

class ShopifyMetafieldMixin:
    """
    Provides helper to determine Shopify metafield type and serialized value.
    """
    def prepare_metafield_payload(self, raw_value):
        if isinstance(raw_value, (dict, list)):
            return 'json_string', json.dumps(raw_value)
        else:
            return 'single_line_text_field', str(raw_value)