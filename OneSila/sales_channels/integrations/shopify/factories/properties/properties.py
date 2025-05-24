import json
from sales_channels.integrations.shopify.factories.mixins import RemoteValueMixin
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
    Creates or upserts a single metafield on a Shopify product using GraphQL.
    """
    remote_model_class = ShopifyProductProperty

    def create_remote(self):
        raw_value = self.get_remote_value()
        self.remote_value = raw_value

        prop = self.local_instance.property
        self.namespace, self.key, self.value, self.metafield_type = self.prepare_metafield_payload(raw_value, prop)

        if self.get_value_only:
            self.remote_instance.remote_value = str(self.remote_value)
            self.remote_instance.save()
            return

        gql = self.api.GraphQL()

        owner_id = (
            self.remote_product.default_variant_id
            if self.remote_product.is_variation
            else self.remote_product.remote_id
        )

        variables = {
            "metafields": [{
                "namespace": self.namespace,
                "key": self.key,
                "value": self.value,
                "type": self.metafield_type,
                "ownerId": owner_id,
            }]
        }

        query = """
        mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
          metafieldsSet(metafields: $metafields) {
            metafields {
              id
              key
              namespace
              value
              type
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        response = gql.execute(query, variables=variables)
        return json.loads(response)

    def serialize_response(self, response):
        if response:
            return response.get("data", {}).get("metafieldsSet", {}).get("metafields", [])[0]
        return {}

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        return self.remote_instance_data

    def post_create_process(self):
        super().post_create_process()
        self.remote_instance.key = self.key


class ShopifyProductPropertyUpdateFactory(
    GetShopifyApiMixin,
    RemoteValueMixin,
    ShopifyMetafieldMixin,
    RemoteProductPropertyUpdateFactory
):
    """
    Updates (or creates) a product metafield using the same GraphQL mutation.
    """
    remote_model_class = ShopifyProductProperty
    create_factory_class = ShopifyProductPropertyCreateFactory

    def update_remote(self):
        raw_value = self.get_remote_value()
        self.remote_value = raw_value

        prop = self.local_instance.property
        self.namespace, self.key, self.value, self.metafield_type = self.prepare_metafield_payload(raw_value, prop)

        if self.remote_instance.namespace != self.namespace:
            self.remote_instance = self.remote_instance.namespace
            self.remote_instance.save()

        gql = self.api.GraphQL()

        owner_id = (
            self.remote_product.default_variant_id
            if self.remote_product.is_variation
            else self.remote_product.remote_id
        )

        variables = {
            "metafields": [{
                "namespace": self.namespace,
                "key": self.key,
                "value": self.value,
                "type": self.metafield_type,
                "ownerId": owner_id,
            }]
        }

        query = """
        mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
          metafieldsSet(metafields: $metafields) {
            metafields {
              id
              key
              namespace
              value
              type
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        response = gql.execute(query, variables=variables)
        return json.loads(response)

    def serialize_response(self, response):
        return response

    def create_remote_instance(self):

        create_factory = ShopifyProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_product,
            api=self.api,
        )
        create_factory.run()

        self.remote_instance = create_factory.remote_instance


class ShopifyProductPropertyDeleteFactory(
    GetShopifyApiMixin,
    RemoteProductPropertyDeleteFactory
):
    """
    Deletes a product metafield by namespace+key using Shopify GraphQL API.
    """
    remote_model_class = ShopifyProductProperty
    delete_remote_instance = True

    def delete_remote(self):
        gql = self.api.GraphQL()

        self.namespace = self.remote_instance.namespace
        self.key = self.remote_instance.key

        owner_id = (
            self.remote_product.default_variant_id
            if self.remote_product.is_variation
            else self.remote_product.remote_id
        )
        self.owner_id = owner_id

        variables = {
            "metafields": [{
                "namespace": self.namespace,
                "key": self.key,
                "ownerId": self.owner_id,
            }]
        }

        query = """
        mutation MetafieldsDelete($metafields: [MetafieldIdentifierInput!]!) {
          metafieldsDelete(metafields: $metafields) {
            deletedMetafields {
              key
              namespace
              ownerId
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        response = gql.execute(query, variables=variables)
        return json.loads(response)

    def serialize_response(self, response):
        return True
