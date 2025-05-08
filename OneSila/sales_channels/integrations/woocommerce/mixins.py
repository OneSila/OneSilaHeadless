from .api import WoocommerceApiWrapper


class GetWoocommerceAPIMixin:
    """
    Mixin to get authenticated Woocommerce API client
    """

    def get_api(self):
        """
        Returns an authenticated Woocommerce API client
        """
        return WoocommerceApiWrapper(
            hostname=self.sales_channel.hostname,
            api_key=self.sales_channel.api_key,
            api_secret=self.sales_channel.api_secret,
            api_version=self.sales_channel.api_version,
            verify_ssl=self.sales_channel.verify_ssl,
            timeout=self.sales_channel.timeout,
        )
