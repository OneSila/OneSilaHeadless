import json
from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyPrice
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException


class ShopifyPriceUpdateFactory(GetShopifyApiMixin, RemotePriceUpdateFactory):
    remote_model_class = ShopifyPrice

    def update_remote(self):
        gql = self.api.GraphQL()

        currency_code = self.to_update_currencies[0]
        price_info = self.price_data.get(currency_code, {})

        if not price_info:
            raise ValueError(f"No price data for currency: {currency_code}")

        variant_payload = {
            "id": self.remote_product.default_variant_id,
        }

        if price_info.get("discount_price"):
            variant_payload["price"] = str(price_info["discount_price"])
            variant_payload["compareAtPrice"] = str(price_info["price"])
        else:
            variant_payload["price"] = str(price_info["price"])
            variant_payload["compareAtPrice"] = None


        query = """
        mutation UpdatePrice($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product {
              id
            }
            productVariants {
              id
              price
              compareAtPrice
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {
            "productId": self.remote_product.remote_id,
            "variants": [variant_payload],
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantsBulkUpdate (price) userErrors: {errors}")

        return data["data"]["productVariantsBulkUpdate"]

    def serialize_response(self, response):
        return response
