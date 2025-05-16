import json

from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughUpdateFactory,
    RemoteMediaProductThroughDeleteFactory,
    RemoteImageDeleteFactory
)
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin, ShopifyMediaPayloadMixin
from sales_channels.integrations.shopify.models.products import ShopifyImageProductAssociation

class ShopifyMediaProductThroughCreateFactory(GetShopifyApiMixin, ShopifyMediaPayloadMixin, RemoteMediaProductThroughCreateFactory):
    """
    Creates a new media entry on Shopify and assigns it to the product or variant.
    Supports get_value_only for bulk usage.
    """
    remote_model_class = ShopifyImageProductAssociation

    def __init__(self, *args, get_value_only=False, **kwargs):
        self.get_value_only = get_value_only
        super().__init__(*args, **kwargs)

    def preflight_check(self):

        if not super().preflight_check():
            return False

        media = self.local_instance.media
        return media.is_image() or media.is_video()

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        self.remote_instance_data['current_position'] = self.local_instance.sort_order
        return self.remote_instance_data

    def create_remote(self):

        self.remote_instance_data = self.prepare_media_payload()
        if self.get_value_only:
            return self.remote_instance_data

        gql = self.api.GraphQL()

        query = """
        mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
          productCreateMedia(media: $media, productId: $productId) {
            media {
              mediaContentType
              alt
              ... on MediaImage {
                id
                image {
                  url
                }
              }
              ... on ExternalVideo {
                id
                originUrl
              }
            }
            mediaUserErrors {
              field
              message
            }
          }
        }
        """

        product_id = self.remote_product.remote_parent_product.remote_id if self.remote_product.is_variation else self.remote_product.remote_id
        variables = {
            "productId": product_id,
            "media": [self.remote_instance_data],
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productCreateMedia", {}).get("mediaUserErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productCreateMedia errors: {errors}")

        media_data = data["data"]["productCreateMedia"]["media"][0]

        # Extract the remote ID and URL
        remote_id = media_data["id"]

        self.remote_instance_data = {
            "id": remote_id,
            "media_type": media_data["mediaContentType"],
            "alt": media_data.get("alt"),
            "current_position": self.local_instance.sort_order,
            "is_main_image": self.local_instance.is_main_image,
        }

        # If variation, assign it to the variant too
        if self.remote_product.is_variation:
            self.assign_to_variant(remote_id)

        return self.remote_instance_data

    def assign_to_variant(self, remote_media_id):
        gql = self.api.GraphQL()
        query = """
        mutation VariantAppendMedia($variantMedia: [ProductVariantAppendMediaInput!]!, $productId: ID!) {
          productVariantAppendMedia(productId: $productId, variantMedia: $variantMedia) {
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {
            "productId": self.remote_product.remote_parent_product.remote_id,
            "variantMedia": [{
                "variantId": self.remote_product.default_variant_id,
                "mediaIds": [remote_media_id],
            }]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantAppendMedia", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantAppendMedia errors: {errors}")

    def serialize_response(self, response):
        return response

class ShopifyMediaProductThroughUpdateFactory(
    GetShopifyApiMixin,
    ShopifyMediaPayloadMixin,
    RemoteMediaProductThroughUpdateFactory
):
    """
    Updates alt text and reorders Shopify media if needed.
    """
    remote_model_class = ShopifyImageProductAssociation
    get_value_only = False

    def __init__(self, *args, get_value_only=False, **kwargs):
        self.get_value_only = get_value_only
        super().__init__(*args, **kwargs)

    def preflight_check(self):

        if not super().preflight_check():
            return False

        media = self.local_instance.media
        return media.is_image() or media.is_video()

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        self.remote_instance_data['is_main_image'] = self.local_instance.is_main_image
        self.remote_instance_data['current_position'] = self.local_instance.sort_order
        return self.remote_instance_data

    def update_remote(self):

        self.remote_instance_data = self.prepare_update_payload()
        if self.get_value_only:
            return self.remote_instance_data

        self._update_alt_text()
        self._reorder_if_needed()
        return self.remote_instance_data

    def prepare_update_payload(self):
        return {
            "id": self.remote_instance.remote_id,
            "alt": getattr(self.local_instance.media.image, 'name', None)
        }

    def _update_alt_text(self):
        gql = self.api.GraphQL()
        query = """
        mutation productUpdateMedia($media: [UpdateMediaInput!]!, $productId: ID!) {
          productUpdateMedia(media: $media, productId: $productId) {
            mediaUserErrors {
              field
              message
            }
          }
        }
        """
        variables = {
            "productId": self.remote_product.remote_id,
            "media": [self.prepare_update_payload()],
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productUpdateMedia", {}).get("mediaUserErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productUpdateMedia errors: {errors}")

    def _reorder_if_needed(self):
        current = self.remote_instance.current_position
        desired = self.local_instance.sort_order

        if current is None or desired is None or current == desired:
            return

        gql = self.api.GraphQL()
        query = """
        mutation productReorderMedia($id: ID!, $moves: [MoveInput!]!) {
          productReorderMedia(id: $id, moves: $moves) {
            job {
              id
              done
            }
            mediaUserErrors {
              code
              field
              message
            }
          }
        }
        """

        variables = {
            "id": self.remote_product.remote_id,
            "moves": [{
                "id": self.remote_instance.remote_id,
                "newPosition": str(desired),
            }]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productReorderMedia", {}).get("mediaUserErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productReorderMedia errors: {errors}")

    def serialize_response(self, response):
        return response

    def needs_update(self):
        return True

class ShopifyMediaProductThroughDeleteFactory(
    GetShopifyApiMixin,
    RemoteMediaProductThroughDeleteFactory
):
    """
    Deletes a Shopify media association via GraphQL.
    Handles both product-level delete and variant-level detach.
    """
    remote_model_class = ShopifyImageProductAssociation
    delete_remote_instance = True

    def delete_remote(self):

        if not self.remote_instance.remote_id:
            return True

        if self.remote_product.is_variation:
            return self._detach_variant_media()
        else:
            return self._delete_product_media()

    def _delete_product_media(self):
        gql = self.api.GraphQL()
        query = """
        mutation productDeleteMedia($productId: ID!, $mediaIds: [ID!]!) {
          productDeleteMedia(productId: $productId, mediaIds: $mediaIds) {
            deletedMediaIds
            product {
              id
            }
            mediaUserErrors {
              code
              field
              message
            }
          }
        }
        """
        variables = {
            "productId": self.remote_product.remote_id,
            "mediaIds": [self.remote_instance.remote_id],
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productDeleteMedia", {}).get("mediaUserErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productDeleteMedia errors: {errors}")

        return data

    def _detach_variant_media(self):
        gql = self.api.GraphQL()
        query = """
        mutation productVariantDetachMedia($productId: ID!, $variantMedia: [ProductVariantDetachMediaInput!]!) {
          productVariantDetachMedia(productId: $productId, variantMedia: $variantMedia) {
            product {
              id
            }
            productVariants {
              id
              media(first: 10) {
                edges {
                  node {
                    preview {
                      image {
                        url
                      }
                    }
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
            "productId": self.remote_product.remote_parent_product.remote_id,
            "variantMedia": [{
                "variantId": self.remote_product.default_variant_id,
                "mediaIds": [self.remote_instance.remote_id],
            }]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantDetachMedia", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantDetachMedia errors: {errors}")

        return data

    def serialize_response(self, response):
        return response

class ShopifyImageDeleteFactory(RemoteImageDeleteFactory):
    """
    Deletes all image associations when the underlying media object is deleted.
    """
    has_remote_media_instance = False
    delete_media_assign_factory = ShopifyMediaProductThroughDeleteFactory
