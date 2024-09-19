from magento.models import Product, ConfigurableProduct
from sales_channels.factories.products.variations import RemoteProductVariationAddFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin


class MagentoProductVariationAddFactory(GetMagentoAPIMixin, RemoteProductVariationAddFactory):

    def update_remote(self):
        self.magento_parent_product: Product = self.api.products.by_sku(self.remote_parent_product.remote_sku)

        if self.configurator_properties is None:
            self.configurator_properties = []
            for remote_property in self.remote_parent_product.configurator.remote_properties:
                magento_property =  self.api.product_attributes.by_code(remote_property.attribute_code)
                self.configurator_properties.append(magento_property)

        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        configurable_prod = ConfigurableProduct(product=self.magento_parent_product, client=self.api)
        configurable_prod.add_child(child_product=self.magento_product, attributes=self.configurator_properties)

    def serialize_response(self, response):
        return {}