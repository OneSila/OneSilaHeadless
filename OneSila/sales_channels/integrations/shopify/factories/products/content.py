import json

from products.models import ProductTranslation
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.products import ShopifyProductContent


class ShopifyProductContentUpdateFactory(GetShopifyApiMixin, RemoteProductContentUpdateFactory):
    remote_model_class = ShopifyProductContent

    def customize_payload(self):

        translation = ProductTranslation.objects.filter(product=self.local_instance, language=self.local_instance.multi_tenant_company.language).first()
        self.payload = {
            "id": self.remote_product.remote_id
        }

        if not self.remote_product.is_variation:
            self.payload.update({
                "title": translation.name,
                "descriptionHtml": translation.description,
                "handle": translation.url_key,
            })

        short_desc = getattr(translation, 'short_description', None)

        if short_desc:
            self.payload["metafields"] = [{
                "namespace": DEFAULT_METAFIELD_NAMESPACE,
                "key": "short_description",
                "type": "multi_line_text_field",
                "value": short_desc
            }]

    def update_remote(self):
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
