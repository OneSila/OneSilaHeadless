from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin


class MagentoSalesChannelViewAssignUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = Product

    def needs_update(self):
        """
        We don't need to compare the payloads this will always be triggered when it needs update
        """
        return True