from magento.models import Product
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoPrice


class MagentoPriceUpdateFactory(GetMagentoAPIMixin, RemotePriceUpdateFactory):
    remote_model_class = MagentoPrice

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.magento_product.price = self.full_price
        self.magento_product.special_price = self.discounted_price
        self.magento_product.save()

    def serialize_response(self, response):
        return {}