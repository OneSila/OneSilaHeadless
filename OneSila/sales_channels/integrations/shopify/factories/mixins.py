import json
import shopify
from django.conf import settings
from properties.models import Property, ProductPropertyTextTranslation


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
            api_key=settings.SHOPIFY_API_KEY,
            secret=settings.SHOPIFY_API_SECRET,
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

class RemoteValueMixin:
    def get_remote_value(self):
        property_type = self.local_property.type
        value = self.local_instance.get_value()

        if property_type in [Property.TYPES.INT, Property.TYPES.FLOAT]:
            return value

        if property_type == Property.TYPES.BOOLEAN:
            return self.get_boolean_value(value)

        if property_type == Property.TYPES.SELECT:
            return self.get_select_value(multiple=False)

        if property_type == Property.TYPES.MULTISELECT:
            return self.get_select_value(multiple=True)

        if property_type in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION]:
            return self.get_translated_values()

        if property_type == Property.TYPES.DATE:
            return self.format_date(value)

        if property_type == Property.TYPES.DATETIME:
            return self.format_datetime(value)

        return None

    def get_boolean_value(self, value):
        return True if value in [True, 'true', '1', 1] else False

    def get_select_value(self, multiple):
        if self.local_property.type == Property.TYPES.MULTISELECT:
            values = self.local_instance.value_multi_select.all()
        else:
            values = [self.local_instance.value_select]

        return [v.value for v in values] if multiple else values[0].value if values else None

    def get_translated_values(self):
        # This can stay as-is unless Shopify wants language mappings (not usually needed)
        default_translation = ProductPropertyTextTranslation.objects.filter(product_property=self.local_instance).first()
        if default_translation:
            return (
                default_translation.value_text if self.local_property.type == Property.TYPES.TEXT
                else default_translation.value_description
            )
        return None

    def format_date(self, date_value):
        return date_value.isoformat()[:10] if date_value else None  # YYYY-MM-DD

    def format_datetime(self, datetime_value):
        return datetime_value.isoformat() if datetime_value else None  # full ISO


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
