from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
    RemoteProductSyncFactory,
)

from sales_channels.factories.products.variations import (
    RemoteProductVariationAddFactory,
    RemoteProductVariationDeleteFactory,
)

from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, \
    WoocommerceProductProperty, WoocommerceProductProperty
from .mixins import SerialiserMixin, WoocommerceProductTypeMixin
from .properties import WooCommerceProductPropertyCreateFactory, \
    WooCommerceProductPropertyUpdateFactory, WooCommerceProductPropertyDeleteFactory
from .media import WooCommerceMediaProductThroughCreateFactory, \
    WooCommerceMediaProductThroughUpdateFactory, WooCommerceMediaProductThroughDeleteFactory
from .ean import WooCommerceEanCodeUpdateFactory
from ..exceptions import DuplicateError
from .properties import WooCommerceProductAttributeMixin
from .media import WooCommerceMediaMixin

import logging
logger = logging.getLogger(__name__)


class WooCommerceProductMixin(WooCommerceMediaMixin, GetWoocommerceAPIMixin, WooCommerceProductAttributeMixin, WoocommerceProductTypeMixin, SerialiserMixin):
    remote_model_class = WoocommerceProduct
    remote_product_property_class = WoocommerceProductProperty
    remote_id_map = 'id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'sku': 'sku',
        # The price fields are not really fields
        # but "magic" and get set during the payload build.
        'price': 'regular_price',
        'discount': 'sale_price',
        'name': 'name',
        'description': 'description',
        'short_description': 'short_description',
    }

    already_exists_exception = DuplicateError

    def get_local_product(self):
        return self.local_instance

    def customize_payload(self):
        """
        Customizes the payload for WooCommerce products
        """
        # Products must be created and updated with the attributes
        # included in the product payload.
        self.apply_attribute_payload()
        self.apply_media_payload()

        if self.local_instance.active:
            self.payload['status'] = 'publish'
            self.payload['catalog_visibility'] = 'visible'
        else:
            self.payload['status'] = 'draft'
            self.payload['catalog_visibility'] = 'hidden'

        if self.is_woocommerce_configurable_product:
            # This also needs the variations to be created.
            self.payload['type'] = 'variable'

        if self.is_woocommerce_simple_product:
            self.payload['type'] = 'simple'

        if self.is_woocommerce_variant_product:
            # No type is passed. Woocom takes care of it.
            pass
            # self.payload['type'] = 'variation'

        return self.payload

    def process_content_translation(self, short_description, description, url_key, remote_language):
        # No translations are supported in woocommerce.
        pass


class WooCommerceProductSyncFactory(WooCommerceProductMixin, RemoteProductSyncFactory):
    remote_model_class = WoocommerceProduct
    remote_product_property_class = WoocommerceProductProperty
    remote_product_property_create_factory = WooCommerceProductPropertyCreateFactory
    remote_product_property_update_factory = WooCommerceProductPropertyUpdateFactory
    remote_product_property_delete_factory = WooCommerceProductPropertyDeleteFactory

    remote_image_assign_create_factory = WooCommerceMediaProductThroughCreateFactory
    remote_image_assign_update_factory = WooCommerceMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = WooCommerceMediaProductThroughDeleteFactory

    remote_eancode_update_factory = WooCommerceEanCodeUpdateFactory

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


class WooCommerceProductCreateFactory(RemoteProductCreateFactory, WooCommerceProductSyncFactory, WoocommerceProductTypeMixin):
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "WooCommerceProductUpdateFactory"

    def perform_non_subclassed_remote_action(self):
        """
        Creates a remote product in WooCommerce.
        """
        if self.is_woocommerce_variant_product:
            logger.debug(f"remote variation instance payload for create: {self.remote_instance.remote_parent_product.__dict__}")
            resp = self.api.create_product_variation(self.remote_instance.remote_parent_product.remote_id, **self.payload)
            logger.debug(f"remote variation instance payload for create response: {resp}")
            return resp

        else:
            logger.debug(f"remote product instance payload for create: {self.remote_instance.__dict__}")
            resp = self.api.create_product(**self.payload)
            logger.debug(f"remote product instance payload for create response: {resp}")
            return resp

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing product by SKU.
        """
        return self.api.get_product_by_sku(self.local_instance.sku)

    def process_product_properties(self):
        """
        Processes each property retrieved from the product and performs the necessary actions,
        such as adding to payload, creating or updating remote instances, etc.
        """
        # Surely we shouldn't just "skip" this factory action?
        # Or does it not matter since the product properties don't really exist?
        pass


class WooCommerceProductUpdateFactory(RemoteProductUpdateFactory, WooCommerceProductSyncFactory, WoocommerceProductTypeMixin):
    # field_mapping = {
    #     'sku': 'sku',
    #     # The price fields are not really fields
    #     # but "magic" and get set during the payload build.
    #     'price': 'regular_price',
    #     'discount': 'sale_price',
    #     'name': 'name',
    #     'description': 'description',
    #     'short_description': 'short_description',
    # }

    create_factory_class = WooCommerceProductCreateFactory

    def perform_remote_action(self):
        """
        Updates a remote product in WooCommerce.
        """
        if self.is_woocommerce_variant_product:
            resp = self.api.update_product_variation(self.remote_instance.remote_parent_product.remote_id, self.remote_instance.remote_id, **self.payload)
            return resp
        else:
            return self.api.update_product(self.remote_instance.remote_id, **self.payload)


class WooCommerceProductDeleteFactory(WooCommerceProductMixin, RemoteProductDeleteFactory):
    delete_remote_instance = True

    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        return self.api.delete_product(self.remote_instance.remote_id)


class WooCommerceProductVariationAddFactory(WooCommerceProductMixin, RemoteProductVariationAddFactory):
    def update(self, *args, **kwargs):
        raise NotImplementedError("WooCommerceProductVariationAddFactory is not implemented")
        return self.api.create_product_variation(self.remote_instance.remote_id, **self.payload)


class WooCommerceProductVariationDeleteFactory(WooCommerceProductMixin, RemoteProductVariationDeleteFactory):
    def delete_remote_instance_process(self, *args, **kwargs):
        raise NotImplementedError("WooCommerceProductVariationAddFactory is not implemented")
        return self.api.delete_product_variation(self.remote_instance.remote_id, self.remote_instance.remote_parent_product.remote_id)
