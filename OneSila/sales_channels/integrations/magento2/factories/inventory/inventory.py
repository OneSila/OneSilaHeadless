from magento.models import Product
from inventory.models import Inventory
from sales_channels.factories.inventory.inventory import RemoteInventoryUpdateFactory
from sales_channels.integrations.magento2.models import MagentoInventory


class MagentoInventoryUpdateFactory(RemoteInventoryUpdateFactory):
    local_model_class = Inventory
    remote_model_class = MagentoInventory

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.magento_product.stock = self.stock
        self.magento_product.save()

    def serialize_response(self, response):
        return {}