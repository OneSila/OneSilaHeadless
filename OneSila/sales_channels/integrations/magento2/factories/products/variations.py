from magento.models import Product, ConfigurableProduct
from sales_channels.factories.products.variations import RemoteProductVariationAddFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProduct


class MagentoProductVariationAddFactory(GetMagentoAPIMixin, RemoteProductVariationAddFactory):

    def get_create_factory_class(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductCreateFactory
        return MagentoProductCreateFactory

    create_factory_class = property(get_create_factory_class)
    remote_model_class = MagentoProduct

    def update_remote(self):
        self.magento_parent_product: Product = self.api.products.by_sku(self.remote_parent_product.remote_sku)
        print('------------------------------------------------------------------------------- ?')

        if self.configurator_properties is None:
            self.configurator_properties = []
            for remote_property in self.remote_parent_product.configurator.remote_properties.all():
                magento_property =  self.api.product_attributes.by_code(remote_property.attribute_code)
                self.configurator_properties.append(magento_property)

        print('---------------------------------------------------------------------------- ADD CHILD')
        self.magento_product: Product = self.api.products.by_sku(self.remote_instance.remote_sku)
        configurable_prod = ConfigurableProduct(product=self.magento_parent_product, client=self.api)
        configurable_prod.add_child(child_product=self.magento_product, attributes=self.configurator_properties)

    def serialize_response(self, response):
        return {}