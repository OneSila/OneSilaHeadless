import json
from products.product_types import CONFIGURABLE
from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyEanCode


class ShopifyEanCodeUpdateFactory(GetShopifyApiMixin, RemoteEanCodeUpdateFactory):
    remote_model_class = ShopifyEanCode

    def needs_update(self):

        if self.remote_product.local_instance.type == CONFIGURABLE:
            return False

        self.ean_code_value = self.get_ean_code_value()
        return self.ean_code_value != (self.remote_instance.ean_code or '')

    def update_remote(self):
        gql = self.api.GraphQL()

        query = """
        mutation UpdateBarcode($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product {
              id
            }
            productVariants {
              id
              barcode
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        parent_id = self.remote_product.remote_parent_product.remote_id if self.remote_product.is_variation else self.remote_product.remote_id
        variables = {
            "productId": parent_id,
            "variants": [{
                "id": self.remote_product.default_variant_id,
                "barcode": str(self.ean_code_value) if self.ean_code_value else '',
            }]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)


        errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantsBulkUpdate (barcode) userErrors: {errors}")

        return data["data"]["productVariantsBulkUpdate"]

    def post_update_process(self):
        self.remote_instance.ean_code = self.ean_code_value

    def serialize_response(self, response):
        return response