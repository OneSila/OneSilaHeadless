from magento import get_api

class GetMagentoAPIMixin:
    def get_api(self):
        """
        Retrieves the Magento API client configured for the specific sales channel.
        """
        return get_api(
            domain=self.sales_channel.hostname,
            username=self.sales_channel.host_api_username,
            password=self.sales_channel.host_api_key,
            api_key=self.sales_channel.host_api_key,
            local=not self.sales_channel.verify_ssl,
            user_agent=None,
            authentication_method=self.sales_channel.authentication_method,
            strict_mode=True
        )
