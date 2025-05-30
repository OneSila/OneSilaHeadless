from magento.models import Product
from inventory.models import Inventory
from sales_channels.factories.inventory.inventory import RemoteInventoryUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoInventory


class MagentoInventoryUpdateFactory(GetMagentoAPIMixin, RemoteInventoryUpdateFactory):
    local_model_class = Product
    remote_model_class = MagentoInventory

    def update_remote(self):
        return  # @TODO: Come back after we decide with inventory

        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.magento_product.stock = self.stock
        self.magento_product.save()

    def serialize_response(self, response):
        return {}
