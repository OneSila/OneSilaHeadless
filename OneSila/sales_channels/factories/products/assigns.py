from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin
from sales_channels.models import SalesChannelViewAssign


class RemoteSalesChannelViewAssignUpdateFactory(ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = Product
    local_product_map = 'product'

    def __init__(self, sales_channel, local_instance, api=None):
        self.local_instance = local_instance
        self.sales_channel = sales_channel

        self.remote_instance = self.get_remote_instance()

        super().__init__(sales_channel, local_instance, api=api, remote_product= self.remote_instance, remote_instance= self.remote_instance)


    def get_remote_instance(self):
        return self.remote_model_class.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            is_variation=False, # variations don't have direct sales channel assigned
        )

    def needs_update(self):
        return True