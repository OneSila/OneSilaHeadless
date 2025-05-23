from sales_channels.factories.products.assigns import RemoteSalesChannelViewAssignUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProduct
from sales_channels.models import SalesChannelViewAssign


class MagentoSalesChannelViewAssignUpdateFactory(GetMagentoAPIMixin, RemoteSalesChannelViewAssignUpdateFactory):
    remote_model_class = MagentoProduct

    def fetch_sales_channels_assign(self):
        self.sales_channel_assings = SalesChannelViewAssign.objects.filter(
            sales_channel=self.sales_channel,
            product=self.local_instance,
            sales_channel__active=True
        )

    def add_to_remote_product_if_needed(self):

        for assign in self.sales_channel_assings:
            if assign.remote_product is None:
                assign.remote_product = self.remote_instance
                assign.save()

    def update_remote(self):
        self.fetch_sales_channels_assign()
        self.add_to_remote_product_if_needed()
        view_ids = list(
            map(int, self.sales_channel_assings.values_list('sales_channel_view__remote_id', flat=True))
        )

        magento_instance = self.api.products.by_sku(self.remote_instance.remote_sku)
        magento_instance.views = view_ids
        magento_instance.save()

    def serialize_response(self, response):
        return
