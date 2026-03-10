from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin


class ValidateMiraklCredentialsFactory(GetMiraklAPIMixin):
    """Validate Mirakl credentials and cache account metadata."""

    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel

    def run(self):
        account_info = self.validate_credentials()
        self.sales_channel.raw_data = account_info or {}
        self.sales_channel.save(update_fields=["raw_data"])
        return account_info
