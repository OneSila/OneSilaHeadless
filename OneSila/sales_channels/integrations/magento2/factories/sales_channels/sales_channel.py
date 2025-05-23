from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin


class TryConnection(GetMagentoAPIMixin):
    def __init__(self, sales_channel, **kwargs):
        self.sales_channel = sales_channel
        self.api = self.get_api()
