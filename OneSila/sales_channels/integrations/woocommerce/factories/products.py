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
    WoocommerceProductProperty, WoocommerceProductProperty, WoocommercePrice, \
    WoocommerceProductContent, WoocommerceEanCode, WoocommerceCurrency
from sales_channels.models.products import RemoteProduct
from sales_channels.models.sales_channels import SalesChannelViewAssign
from .mixins import WooCommerceUpdateRemoteProductMixin, WoocommerceProductTypeMixin, \
    WooCommercePayloadMixin, SerialiserMixin, GetWoocommerceAPIMixin
from .properties import WooCommerceProductPropertyCreateFactory, \
    WooCommerceProductPropertyUpdateFactory, WooCommerceProductPropertyDeleteFactory
from .media import WooCommerceMediaProductThroughCreateFactory, \
    WooCommerceMediaProductThroughUpdateFactory, WooCommerceMediaProductThroughDeleteFactory
from .ean import WooCommerceEanCodeUpdateFactory
from ..exceptions import DuplicateError, FailedToDeleteError

import logging
logger = logging.getLogger(__name__)


class WooCommerceProductMixin(WooCommerceUpdateRemoteProductMixin, WooCommercePayloadMixin):
    remote_model_class = WoocommerceProduct
    remote_price_class = WoocommercePrice

    remote_product_property_class = WoocommerceProductProperty
    remote_product_content_class = WoocommerceProductContent
    remote_product_eancode_class = WoocommerceEanCode

    already_exists_exception = DuplicateError

    def get_local_product(self):
        return self.local_instance

    def process_content_translation(self, short_description, description, url_key, remote_language):
        # If you don't trigger set_content the mirror model will not be created.
        self.set_content()


class WooCommerceProductSyncFactory(WooCommerceProductMixin, RemoteProductSyncFactory):
    remote_model_class = WoocommerceProduct
    remote_price_class = WoocommercePrice

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

    def perform_remote_action(self):
        """
        Updates a remote product in WooCommerce.
        """

        if self.is_create:
            super().perform_remote_action()
            return

        return self.update_remote_product()
        # if self.is_woocommerce_variant_product:
        #     parent_id = self.remote_instance.remote_parent_product.remote_id
        #     variant_id = self.remote_instance.remote_id
        #     return self.api.update_product_variation(parent_id, variant_id, **self.payload)
        # else:
        #     product_id = self.remote_instance.remote_id
        #     return self.api.update_product(product_id, **self.payload)

    # Use the getter methods within the class where needed
    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    add_variation_factory = property(get_add_variation_factory)

    def get_variation_sku(self):
        return self.local_instance.sku


class WooCommerceProductCreateFactory(WooCommerceProductSyncFactory, WoocommerceProductTypeMixin, RemoteProductCreateFactory):
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "WooCommerceProductUpdateFactory"
    sync_product_factory = WooCommerceProductSyncFactory

    remote_price_class = WoocommercePrice
    remote_product_content_class = WoocommerceProductContent
    remote_product_eancode_class = WoocommerceEanCode

    def __init__(self, *args, is_variation_add: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_variation_add = is_variation_add

    def perform_non_subclassed_remote_action(self):
        """
        Creates a remote product in WooCommerce.
        """
        if self.is_woocommerce_variant_product:
            if getattr(self, "is_variation_add", False):
                parent_factory = WooCommerceProductUpdateFactory(
                    sales_channel=self.sales_channel,
                    local_instance=self.parent_local_instance,
                    remote_instance=self.remote_instance.remote_parent_product,
                    api=self.api,
                )
                parent_factory.run()
            resp = self.api.create_product_variation(
                self.remote_instance.remote_parent_product.remote_id,
                **self.payload,
            )
        else:
            resp = self.api.create_product(**self.payload)

        self.set_remote_id(resp)
        # Extract remote_id and remote_sku from the response
        self.remote_instance.remote_sku = self.sku

        # Save the RemoteProduct instance with updated remote_id and remote_sku
        self.remote_instance.save()

        return resp

    def fetch_existing_remote_data(self):
        """
        Attempts to fetch an existing product by SKU.
        """
        return self.api.get_product_by_sku(self.local_instance.sku)


class WooCommerceProductUpdateFactory(WooCommerceProductSyncFactory, WoocommerceProductTypeMixin, RemoteProductUpdateFactory):
    create_factory_class = WooCommerceProductCreateFactory


class WooCommerceProductDeleteFactory(SerialiserMixin, GetWoocommerceAPIMixin, RemoteProductDeleteFactory):
    delete_remote_instance = True
    remote_model_class = WoocommerceProduct

    def get_local_product(self):
        return self.remote_instance.local_instance

    def delete_remote(self):
        """
        Deletes a remote product in WooCommerce.
        """
        try:
            if self.remote_instance.is_variation:
                return self.api.delete_product_variation(self.remote_instance.remote_id, self.remote_instance.remote_parent_product.remote_id)
            else:
                return self.api.delete_product(self.remote_instance.remote_id)
        except FailedToDeleteError:
            pass


class WooCommerceProductVariationAddFactory(SerialiserMixin, GetWoocommerceAPIMixin, RemoteProductVariationAddFactory):
    """
    After a variation is created, this factory will assign that variation to the configurable product.
    However, in Woocommerce this is not relevant. So we override update_remote trigger a new product update.
    """
    remote_model_class = WoocommerceProduct
    create_factory_class = WooCommerceProductCreateFactory

    def preflight_check(self):
        """Extends the base check to ensure the parent product is updated when
        a new variation is added."""
        if self.skip_checks:
            return True

        # Check for SalesChannelViewAssign associated with the remote parent product
        parent_assign_exists = SalesChannelViewAssign.objects.filter(
            product=self.parent_product,
            sales_channel=self.sales_channel,
        ).exists()

        if not parent_assign_exists:
            return False

        try:
            self.remote_parent_product = RemoteProduct.objects.get(
                local_instance=self.parent_product,
                sales_channel=self.sales_channel,
            )
        except RemoteProduct.DoesNotExist:
            return False

        try:
            self.remote_instance = RemoteProduct.objects.get(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel,
                remote_parent_product=self.remote_parent_product,
            )
        except RemoteProduct.DoesNotExist:
            if self.create_if_not_exists:
                factory = self.create_factory_class(
                    sales_channel=self.sales_channel,
                    local_instance=self.local_instance,
                    parent_local_instance=self.parent_product,
                    remote_parent_product=self.remote_parent_product,
                    api=self.api,
                    is_variation_add=True,
                )
                factory.run()
                self.remote_instance = factory.remote_instance
            else:
                raise

        return True

    def update_remote(self, *args, **kwargs):
        # Woocommerce doesnt need assinging a variation.
        # This happens by default thorugh the create_factory_class.
        # Do nothing is the right course of action.
        pass


class WooCommerceProductVariationDeleteFactory(SerialiserMixin, GetWoocommerceAPIMixin, RemoteProductVariationDeleteFactory):
    remote_model_class = WoocommerceProduct

    def delete_remote_instance_process(self, *args, **kwargs):
        try:
            return self.api.delete_product_variation(self.remote_instance.remote_id, self.remote_instance.remote_parent_product.remote_id)
        except FailedToDeleteError:
            # this never existed so we can just pass this
            pass
