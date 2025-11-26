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

        lang = self.language or self.local_instance.multi_tenant_company.language

        channel_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=self.sales_channel,
        ).first()

        default_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=None,
        ).first()

        self.payload = {"id": self.remote_product.remote_id}

        if not self.remote_product.is_variation:
            title = None
            description_html = None
            handle = None

            if channel_translation:
                title = channel_translation.name or None
                description_html = channel_translation.description
                if description_html == "<p><br></p>":
                    description_html = ""
                handle = channel_translation.url_key or None

            if not title and default_translation:
                title = default_translation.name

            if (not description_html) and default_translation:
                description_html = default_translation.description
                if description_html == "<p><br></p>":
                    description_html = ""

            if not handle and default_translation:
                handle = default_translation.url_key

            self.payload.update({
                "title": title,
                "descriptionHtml": description_html,
                "handle": handle,
            })

        short_desc = None
        if channel_translation:
            short_desc = getattr(channel_translation, "short_description", None)
        if (not short_desc) and default_translation:
            short_desc = getattr(default_translation, "short_description", None)
        if short_desc == "<p><br></p>":
            short_desc = ""

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
