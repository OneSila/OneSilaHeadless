from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin


class TryConnection(GetWoocommerceAPIMixin):
    def __init__(self, sales_channel, **kwargs):
        self.sales_channel = sales_channel
        self.api = self.get_api()

    def try_connection(self):
        return self.api.try_connection()
