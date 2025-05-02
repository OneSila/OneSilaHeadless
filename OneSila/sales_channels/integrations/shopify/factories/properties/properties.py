import json

from sales_channels.integrations.magento2.factories.mixins import RemoteValueMixin
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin, ShopifyMetafieldMixin
from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyUpdateFactory,
    RemoteProductPropertyDeleteFactory
)
from sales_channels.integrations.shopify.models.properties import ShopifyProductProperty


class ShopifyProductPropertyCreateFactory(
    GetShopifyApiMixin,
    RemoteValueMixin,
    ShopifyMetafieldMixin,
    RemoteProductPropertyCreateFactory
):
    """
    Creates or upserts a single metafield on a Shopify product, for one ProductProperty.
    """
    remote_model_class = ShopifyProductProperty

    def create_remote(self):
        # session active via base
        product = self.api.Product.find(self.remote_product.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_product.remote_id}")

        # Determine key and raw value using RemoteValueMixin
        key = self.local_instance.property.internal_name
        raw_value = self.get_remote_value()
        mf_type, value = self.prepare_metafield_payload(raw_value)

        mf = self.api.Metafield({
            'namespace': DEFAULT_METAFIELD_NAMESPACE,
            'key':       key,
            'value':     value,
            'type':      mf_type,
        })
        product.add_metafield(mf)

        return mf

    def serialize_response(self, response):
        # response is the Metafield instance
        return response.to_dict()


class ShopifyProductPropertyUpdateFactory(
    GetShopifyApiMixin,
    RemoteValueMixin,
    ShopifyMetafieldMixin,
    RemoteProductPropertyUpdateFactory
):
    """
    Updates an existing product metafield by namespace+key.
    """
    remote_model_class = ShopifyProductProperty
    create_factory_class = ShopifyProductPropertyCreateFactory

    def update_remote(self):

        product = self.api.Product.find(self.remote_product.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_product.remote_id}")

        # Determine key and raw value using RemoteValueMixin
        key = self.local_instance.property.internal_name
        raw_value = self.get_remote_value()
        mf_type, value = self.prepare_metafield_payload(raw_value)

        mf = self.api.Metafield({
            'namespace': DEFAULT_METAFIELD_NAMESPACE,
            'key':       key,
            'value':     value,
            'type':      mf_type,
        })
        product.add_metafield(mf)
        return mf

    def serialize_response(self, response):
        return response.to_dict()


class ShopifyProductPropertyDeleteFactory(
    GetShopifyApiMixin,
    RemoteProductPropertyDeleteFactory
):
    """
    Deletes a product metafield by namespace+key.
    """
    remote_model_class = ShopifyProductProperty
    delete_remote_instance = True

    def delete_remote(self):
        product = self.api.Product.find(self.remote_product.remote_id)
        if not product:
            return True  # already gone or product missing

        # Fetch all metafields, find ours
        mfs = product.metafields()
        key = self.local_instance.property.internal_name
        to_delete = [m for m in mfs if m.namespace == DEFAULT_METAFIELD_NAMESPACE and m.key == key]
        for mf in to_delete:
            mf.destroy()
        return True

    def serialize_response(self, response):
        return True
