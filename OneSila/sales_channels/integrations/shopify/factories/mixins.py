import json
import shopify
from django.conf import settings
from properties.models import Property
from sales_channels.factories.value_mixins import RemoteValueMixin


class GetShopifyApiMixin:
    """
    Mixin to initialize and activate a Shopify session using the shop_url,
    api_version, and access_token stored on the ShopifySalesChannel.
    Also provides a method to clear the session.
    """

    def preflight_process(self):
        pass

    def get_api(self):
        # Configure your app credentials (once per process)
        shopify.Session.setup(
            api_key=self.sales_channel.api_key,
            secret=self.sales_channel.api_secret,
        )

        # Create and activate a session for the specific shop
        session = shopify.Session(
            self.sales_channel.hostname,
            settings.SHOPIFY_API_VERSION,
            self.sales_channel.access_token,
        )
        shopify.ShopifyResource.activate_session(session)
        return shopify

    def clear_api(self):
        """
        Terminates the current Shopify session, clearing out any activated credentials.
        """
        shopify.ShopifyResource.clear_session()
        self.api = None


class ShopifyRemoteValueMixin(RemoteValueMixin):
    pass


class ShopifyMetafieldMixin:
    """
    Prepares the complete Shopify metafield payload.
    Maps internal property types to Shopify metafield types.
    """

    INTERNAL_TYPE_TO_SHOPIFY_TYPE = {
        Property.TYPES.INT: 'number_integer',
        Property.TYPES.FLOAT: 'number_decimal',
        Property.TYPES.TEXT: 'single_line_text_field',
        Property.TYPES.DESCRIPTION: 'multi_line_text_field',
        Property.TYPES.BOOLEAN: 'boolean',
        Property.TYPES.DATE: 'date',
        Property.TYPES.DATETIME: 'date_time',
        Property.TYPES.SELECT: 'single_line_text_field',
        Property.TYPES.MULTISELECT: 'json_string',
    }

    def prepare_metafield_payload(self, raw_value, prop):
        from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE

        internal_type = prop.type
        key = prop.internal_name
        namespace = DEFAULT_METAFIELD_NAMESPACE
        shopify_type = self.INTERNAL_TYPE_TO_SHOPIFY_TYPE.get(internal_type, 'single_line_text_field')

        if internal_type == Property.TYPES.MULTISELECT:
            value = json.dumps(raw_value)  # list of strings expected

        else:
            value = str(raw_value)

        return namespace, key, value, shopify_type


class ShopifyMediaPayloadMixin:
    def prepare_media_payload(self):
        media = self.local_instance.media

        if media.is_video() and media.video_url:
            media_type = "EXTERNAL_VIDEO"
            original_source = media.video_url
        elif media.is_image() and media.image_web_url:
            media_type = "IMAGE"
            original_source = media.image_web_url
        else:
            raise ValueError("Unsupported or missing media source.")

        alt_text = getattr(media.image, 'name', None) if media.is_image() else None

        return {
            "originalSource": original_source,
            "alt": alt_text,
            "mediaContentType": media_type,
        }
