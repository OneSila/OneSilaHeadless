from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceRemoteLanguage


class SerialiserMixin:
    """
    Mixin providing common serialization methods for the woocommerce integration.
    """

    def serialize_response(self, response):
        return response


class WoocommerceSalesChannelLanguageMixin:
    """expose the language of the sales channel"""
    @property
    def sales_channel_assign_language(self):
        """self.language doesnt seem to be available everywhere. So let's fetch it here."""
        language = WoocommerceRemoteLanguage.objects.get(
            sales_channel=self.remote_instance.sales_channel)
        return language.local_instance


class WoocommerceProductTypeMixin:
    """
    This mixin will give you access to:
    - is_woocommerce_simple_product
    - is_woocommerce_configurable_product
    - is_woocommerce_variant_product
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_woocomerce_product_types()

    def run(self, *args, **kwargs):
        self.set_woocomerce_product_types()
        super().run(*args, **kwargs)

    def get_local_product(self):
        return self.remote_product.local_instance

    def remote_product_is_variation(self):
        try:
            return self.is_variation
        except AttributeError:
            return False

    def set_woocomerce_product_types(self):
        product = self.get_local_product()
        is_variation = self.remote_product_is_variation()

        self.is_woocommerce_simple_product = False
        self.is_woocommerce_configurable_product = False
        self.is_woocommerce_variant_product = False

        if product.is_configurable():
            self.is_woocommerce_configurable_product = True
        elif product.is_simple():
            if is_variation:
                self.is_woocommerce_variant_product = True
            else:
                self.is_woocommerce_simple_product = True
        else:
            raise ValueError(f"Product {product} is not configurable or simple. Configure other types.")
