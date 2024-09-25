import logging
from sales_channels.factories.products.products import RemoteProductSyncFactory, RemoteProductCreateFactory, RemoteProductDeleteFactory, \
    RemoteProductUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.factories.products.images import MagentoMediaProductThroughCreateFactory, MagentoMediaProductThroughUpdateFactory, \
    MagentoMediaProductThroughDeleteFactory
from sales_channels.integrations.magento2.factories.properties.properties import MagentoProductPropertyCreateFactory, MagentoProductPropertyUpdateFactory, \
    MagentoProductPropertyDeleteFactory
from sales_channels.integrations.magento2.models import MagentoProduct, MagentoInventory, MagentoPrice, MagentoProductContent, \
    MagentoProductProperty
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet
from magento.models import Product as MagentoApiProduct

from sales_channels.models import SalesChannelViewAssign

logger = logging.getLogger(__name__)

class MagentoProductSyncFactory(GetMagentoAPIMixin, RemoteProductSyncFactory):
    remote_model_class = MagentoProduct
    remote_product_property_class = MagentoProductProperty
    remote_product_property_create_factory = MagentoProductPropertyCreateFactory
    remote_product_property_update_factory = MagentoProductPropertyUpdateFactory
    remote_product_property_delete_factory = MagentoProductPropertyDeleteFactory

    remote_image_assign_create_factory = MagentoMediaProductThroughCreateFactory
    remote_image_assign_update_factory = MagentoMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = MagentoMediaProductThroughDeleteFactory

    def get_sync_product_factory(self):
        return MagentoProductSyncFactory

    def get_create_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductCreateFactory
        return MagentoProductCreateFactory

    def get_delete_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductDeleteFactory
        return MagentoProductDeleteFactory

    def get_add_variation_factory(self):
        # Move import inside the method
        from sales_channels.integrations.magento2.factories.products import MagentoProductVariationAddFactory
        return MagentoProductVariationAddFactory


    # Use the getter methods within the class where needed
    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    add_variation_factory = property(get_add_variation_factory)
    accepted_variation_already_exists_error = Exception # @TODO: Figure it out (or create on the wrapper) the real exception

    field_mapping = {
        'name': 'name',
        'sku': 'sku',
        'type': 'type_id',
        'active': 'status',
        'stock': 'stock',
        'allow_backorder': 'backorders',
        'visibility': 'visibility',
        'content': 'content',
        'assigns': 'views',
        'price': 'price',
        'discount': 'special_price',
        'url_key': 'url_key',
        'description': 'description',
        'short_description': 'short_description',
    }

    # Remote product types, to be set in specific layer implementations
    REMOTE_TYPE_SIMPLE = MagentoApiProduct.PRODUCT_TYPE_SIMPLE
    REMOTE_TYPE_CONFIGURABLE = MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE


    def get_unpacked_product_properties(self):
        custom_attributes = {}
        for remote_product_property in self.remote_product_properties:
            custom_attributes[remote_product_property.remote_property.attribute_code] = remote_product_property.remote_value

        return custom_attributes

    def set_visibility(self):
        if self.is_variation:
            self.set_variation_visibility()
        else:
            self.visibility = MagentoApiProduct.VISIBILITY_BOTH

        self.add_field_in_payload('visibility', self.visibility)

    def set_variation_visibility(self):
        self.visibility = MagentoApiProduct.VISIBILITY_NOT_VISIBLE

    def set_assigns(self):
        if self.is_variation:
            self.set_variation_assigns()
        else:
            self.assigns = list(
                map(int, SalesChannelViewAssign.objects.filter(
                    sales_channel=self.sales_channel,
                    product=self.local_instance
                ).values_list('sales_channel_view__remote_id', flat=True))
            )
        self.add_field_in_payload('assigns', self.assigns)


    def set_variation_assigns(self):
        self.assigns = list(
            map(int, SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.parent_local_instance
            ).values_list('sales_channel_view__remote_id', flat=True))
        )

    def set_stock(self):
        if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
            self.stock = None
        else:
            self.stock = self.local_instance.inventory.salable()

        self.add_field_in_payload('stock', self.stock)

    def set_price(self):
        if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
            self.price, self.discount = None, None
        else:
            self.price, self.discount = self.local_instance.get_price_for_sales_channel(self.sales_channel)

            # Convert price and discount to float if they are not None
            if self.price is not None:
                self.price = float(self.price)
            if self.discount is not None:
                self.discount = float(self.discount)

        self.add_field_in_payload('price', self.price)
        self.add_field_in_payload('discount', self.discount)


    def customize_payload(self):
        attribute_set = MagentoAttributeSet.objects.get(local_instance=self.rule, sales_channel=self.sales_channel)
        self.payload['attribute_set_id'] = attribute_set.remote_id

    def perform_remote_action(self):
        self.magento_product: MagentoApiProduct = self.api.products.by_sku(self.remote_instance.remote_sku)

        for key, value in self.payload.items():
            if value != getattr(self.magento_product, key):
                setattr(self.magento_product, key, value)

        self.magento_product.save(scope='all')
        self.magento_product.update_custom_attributes(self.get_unpacked_product_properties())

    def process_content_translation(self, short_description, description, url_key, remote_language):
        self.magento_product.short_description = short_description
        self.magento_product.description = description
        self.magento_product.url_key = url_key
        self.magento_product.save(scope=remote_language.sales_channel_view.code)

class MagentoProductUpdateFactory(RemoteProductUpdateFactory, MagentoProductSyncFactory):
    pass

class MagentoProductCreateFactory(RemoteProductCreateFactory, MagentoProductSyncFactory):
    remote_inventory_class = MagentoInventory
    remote_price_class = MagentoPrice
    remote_product_content_class = MagentoProductContent
    remote_id_map = 'id'

    api_package_name = 'products'
    api_method_name = 'create'

    def get_sync_product_factory(self):
        return MagentoProductSyncFactory

    sync_product_factory = property(get_sync_product_factory)

    def get_saleschannel_remote_object(self, sku):
        return self.api.products.by_sku(sku)

    def customize_payload(self):
        super().customize_payload()
        extra_data = {'custom_attributes': self.get_unpacked_product_properties()}
        self.payload = {'data': self.payload, 'extra_data': extra_data}

    def serialize_response(self, response):
        self.magento_product = response
        return response.to_dict()

class MagentoProductDeleteFactory(GetMagentoAPIMixin, RemoteProductDeleteFactory):
    remote_model_class = MagentoProduct
    delete_remote_instance = True

    def get_delete_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductDeleteFactory
        return MagentoProductDeleteFactory

    remote_delete_factory = property(get_delete_product_factory)

    def delete_remote(self):
        magento_instance = self.api.products.by_sku(self.remote_instance.remote_sku)
        return magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False