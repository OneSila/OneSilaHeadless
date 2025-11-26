from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models.products import MagentoEanCode


class MagentoEanCodeUpdateFactory(GetMagentoAPIMixin, RemoteEanCodeUpdateFactory):
    """
    Magento-specific factory for updating remote EAN codes.
    Inherits from RemoteEanCodeUpdateFactory and implements Magento API logic.
    """
    remote_model_class = MagentoEanCode

    def post_update_process(self):
        self.remote_instance.ean_code = self.ean_code_value

    def needs_update(self):
        self.ean_code_value = self.get_ean_code_value()

        return self.ean_code_value != self.remote_instance.ean_code

    def update_remote(self):
        self.magento_product = self.api.products.by_sku(self.remote_product.remote_sku)

        ean_attr = self.integration.ean_code_attribute
        self.magento_product.update_custom_attributes({ean_attr: self.ean_code_value})

    def serialize_response(self, response):
        return self.magento_product.to_dict()
