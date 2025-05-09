from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
    RemoteProductSyncFactory,
)

from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, \
    WoocommerceProductProperty, WoocommerceProductProperty
from .mixins import SerialiserMixin
from .properties import WooCommerceProductPropertyCreateFactory, \
    WooCommerceProductPropertyUpdateFactory, WooCommerceProductPropertyDeleteFactory
from .media import WooCommerceMediaProductThroughCreateFactory, \
    WooCommerceMediaProductThroughUpdateFactory, WooCommerceMediaProductThroughDeleteFactory
from ..exceptions import DuplicateError


class WooCommerceProductMixin(SerialiserMixin):
    remote_model_class = WoocommerceProduct
    remote_product_property_class = WoocommerceProductProperty
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'sku': 'sku',
    }
    already_exists_exception = DuplicateError

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce products
        """
        # FIXME: This should be set on the sales-channel.
        language = self.multi_tenant_company.language
        name = self.local_instance._get_translated_value(
            field_name='name',
            language=language,
            related_name='translations'
        )
        short_description = self.local_instance._get_translated_value(
            field_name='short_description',
            language=language,
            related_name='translations'
        )
        description = self.local_instance._get_translated_value(
            field_name='description',
            language=language,
            related_name='translations'
        )

        self.payload['name'] = name
        self.payload['short_description'] = short_description
        self.payload['description'] = description

        price = 0.9
        sale_price = 0.8
        self.payload['regular_price'] = price
        self.payload['sale_price'] = sale_price

        if self.local_instance.active:
            self.payload['status'] = 'publish'
            self.payload['visibility'] = 'visible'
        else:
            self.payload['status'] = 'draft'
            self.payload['visibility'] = 'hidden'

        if self.local_instance.is_configurable():
            # This also needs the variations to be created.
            self.payload['type'] = 'variable'
        else:
            self.payload['type'] = 'simple'

        return self.payload


class WooCommerceProductSyncFactory(WooCommerceProductMixin, GetWoocommerceAPIMixin, RemoteProductSyncFactory):
    remote_model_class = WoocommerceProduct
    remote_product_property_class = WoocommerceProductProperty
    remote_product_property_create_factory = WooCommerceProductPropertyCreateFactory
    remote_product_property_update_factory = WooCommerceProductPropertyUpdateFactory
    remote_product_property_delete_factory = WooCommerceProductPropertyDeleteFactory

    remote_image_assign_create_factory = WooCommerceMediaProductThroughCreateFactory
    remote_image_assign_update_factory = WooCommerceMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = WooCommerceMediaProductThroughDeleteFactory

    # remote_eancode_update_factory = MagentoEanCodeUpdateFactory

    def get_sync_product_factory(self):
        return WooCommerceProductSyncFactory

    def get_create_product_factory(self):
        from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductCreateFactory
        return WooCommerceProductCreateFactory

    def get_delete_product_factory(self):
        from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductDeleteFactory
        return WooCommerceProductDeleteFactory

    def get_add_variation_factory(self):
        from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductVariationAddFactory
        return WooCommerceProductVariationAddFactory

    # Use the getter methods within the class where needed
    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    add_variation_factory = property(get_add_variation_factory)

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
        'vat_rate': 'tax_class_id',
        'url_key': 'url_key',
        'description': 'description',
        'short_description': 'short_description',
    }

    # Remote product types, to be set in specific layer implementations
    # REMOTE_TYPE_SIMPLE = MagentoApiProduct.PRODUCT_TYPE_SIMPLE
    # REMOTE_TYPE_CONFIGURABLE = MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE


class WooCommerceProductCreateFactory(WooCommerceProductMixin, GetWoocommerceAPIMixin, RemoteProductCreateFactory):
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "WooCommerceProductUpdateFactory"

    def create_remote(self):
        """
        Creates a remote product in WooCommerce.
        """
        return self.api.create_product(**self.payload)

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing product by SKU.
        """
        return self.api.get_product_by_sku(self.local_instance.sku)


class WooCommerceProductUpdateFactory(WooCommerceProductMixin, GetWoocommerceAPIMixin, RemoteProductUpdateFactory):
    create_factory_class = WooCommerceProductCreateFactory

    def update_remote(self):
        """
        Updates a remote product in WooCommerce.
        """
        return self.api.update_product(self.remote_instance.remote_id, **self.payload)


class WooCommerceProductDeleteFactory(WooCommerceProductMixin, GetWoocommerceAPIMixin, RemoteProductDeleteFactory):
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.api.delete_product(self.remote_instance.remote_id)
