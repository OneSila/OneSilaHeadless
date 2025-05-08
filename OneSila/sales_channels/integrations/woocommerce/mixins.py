from .api import WoocommerceApiWrapper


class GetWoocommerceAPIMixin:
    """
    Mixin to get authenticated Woocommerce API client
    """

    def get_api_client(self):
        """
        Returns an authenticated Woocommerce API client
        """
        return WoocommerceApiWrapper(
            url=self.sales_channel.hostname,
            consumer_key=self.sales_channel.api_key,
            consumer_secret=self.sales_channel.api_secret,
            version=self.sales_channel.api_version,
            verify_ssl=self.sales_channel.verify_ssl,
            timeout=self.sales_channel.timeout,
        )
