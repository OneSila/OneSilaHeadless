from itertools import product

from sales_channels.factories.products.assigns import MagentoSalesChannelViewAssignUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoSalesChannelViewAssign


class MagentoSalesChannelAssignUpdateFactory(GetMagentoAPIMixin, MagentoSalesChannelViewAssignUpdateFactory):
    remote_model_class = MagentoSalesChannelViewAssign

    def update_remote(self):
        self.magento_instance =self.api.products.by_sku(self.remote_instance.remote_sku)
        view_ids = list(
            map(int, MagentoSalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.remote_instance.product
            ).values_list('sales_channel_view__remote_id', flat=True))
        )

        self.magento_instance.views = view_ids
        self.magento_instance.save()

    def serialize_response(self, response):
        return self.magento_instance.to_dict()