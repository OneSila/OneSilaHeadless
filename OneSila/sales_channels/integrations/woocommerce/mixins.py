from woocommerce import API


class GetWoocommerceAPIMixin:
    """
    Mixin to get authenticated Woocommerce API client
    """

    def get_api_client(self):
        """
        Returns an authenticated Woocommerce API client
        """
        return API(
            url=self.sales_channel.api_url,
            consumer_key=self.sales_channel.api_key,
            consumer_secret=self.sales_channel.api_secret,
            version=self.sales_channel.api_version
        )
