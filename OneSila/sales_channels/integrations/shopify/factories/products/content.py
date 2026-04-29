import json

from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.helpers import build_content_payload
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProductContent


class ShopifyProductContentUpdateFactory(GetShopifyApiMixin, RemoteProductContentUpdateFactory):
    remote_model_class = ShopifyProductContent

    def customize_payload(self):
        content_payload = build_content_payload(
            product=self.local_instance,
            sales_channel=self.sales_channel,
            language=self.language or self.local_instance.multi_tenant_company.language,
        )

        self.payload = {"id": self.remote_product.remote_id}

        if not self.remote_product.is_variation:
            self.payload.update({
                "title": content_payload.get("name"),
                "descriptionHtml": content_payload.get("description"),
                "handle": content_payload.get("urlKey"),
            })

        short_desc = content_payload.get("shortDescription")
        if short_desc:
            self.payload["metafields"] = [
                {
                    "namespace": DEFAULT_METAFIELD_NAMESPACE,
                    "key": "short_description",
                    "type": "multi_line_text_field",
                    "value": short_desc,
                }
            ]

    def update_remote(self):

        if self.remote_product.is_variation:
            return {}

        gql = self.api.GraphQL()

        query = """
        mutation productUpdate($product: ProductUpdateInput!) {
          productUpdate(product: $product) {
            product {
              id
              title
              descriptionHtml
              handle
              metafields(first: 5) {
                edges {
                  node {
                    id
                    key
                    namespace
                    type
                    value
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {
            "product": self.payload
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productUpdate userErrors: {errors}")

        return data["data"]["productUpdate"]["product"]

    def serialize_response(self, response):
        return response
