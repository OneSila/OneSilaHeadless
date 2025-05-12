import json

from media.models import MediaProductThrough, Media
from products.models import Product
from sales_channels.factories.products.products import (
    RemoteProductSyncFactory,
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
)
from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE, ACTIVE_STATUS, NON_ACTIVE_STATUS, \
    ALLOW_BACKORDER_CONTINUE, ALLOW_BACKORDER_DENY, MEDIA_FRAGMENT, get_metafields
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyProductProperty
from sales_channels.integrations.shopify.models.products import ShopifyProduct, ShopifyEanCode, ShopifyPrice, \
    ShopifyProductContent, ShopifyImageProductAssociation
from sales_channels.integrations.shopify.factories.products.eancodes import ShopifyEanCodeUpdateFactory
from sales_channels.integrations.shopify.factories.products.images import (
    ShopifyMediaProductThroughCreateFactory,
    ShopifyMediaProductThroughUpdateFactory,
    ShopifyMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.shopify.factories.properties.properties import (
    ShopifyProductPropertyCreateFactory,
    ShopifyProductPropertyUpdateFactory,
    ShopifyProductPropertyDeleteFactory,
)
import logging

logger = logging.getLogger(__name__)


class ShopifyProductSyncFactory(GetShopifyApiMixin, RemoteProductSyncFactory):
    remote_model_class = ShopifyProduct

    # Sub-factories for images, metafields, EAN, etc.
    remote_image_assign_create_factory = ShopifyMediaProductThroughCreateFactory
    remote_image_assign_update_factory = ShopifyMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = ShopifyMediaProductThroughDeleteFactory

    remote_product_property_class = ShopifyProductProperty
    remote_product_property_create_factory = ShopifyProductPropertyCreateFactory
    remote_product_property_update_factory = ShopifyProductPropertyUpdateFactory
    remote_product_property_delete_factory = ShopifyProductPropertyDeleteFactory

    remote_eancode_update_factory = ShopifyEanCodeUpdateFactory

    sync_product_factory   = property(lambda self: ShopifyProductSyncFactory)
    create_product_factory = property(lambda self: ShopifyProductCreateFactory)
    delete_product_factory = property(lambda self: ShopifyProductDeleteFactory)
    add_variation_factory  = property(lambda self: ShopifyProductSyncFactory)

    # Local field → Shopify REST API field mapping
    field_mapping = {
        'name': 'title',
        'url_key': 'handle',
        'description': 'descriptionHtml',
        'content': 'content',
    }

    variant_payload = {
        'inventoryItem': {}
    }
    metafields = []
    tags = []
    medias = []

    def set_sku(self):
        self.variant_payload['inventoryItem']['sku'] = self.local_instance.sku
        self.variant_payload['inventoryItem']['tracked'] = True

    def set_active(self):
        self.payload['status'] = ACTIVE_STATUS if self.local_instance.active else NON_ACTIVE_STATUS

    def set_allow_backorder(self):
        self.variant_payload['inventoryPolicy'] = ALLOW_BACKORDER_CONTINUE if self.local_instance.allow_backorder else ALLOW_BACKORDER_DENY

    def set_vendor(self):
        if self.sales_channel.vendor_property:
            vendor_product_property = self.product_properties.filter(property=self.sales_channel.vendor_property).first()

            if vendor_product_property:
                self.payload['vendor'] = vendor_product_property.value_select.value

    def set_price(self):
        super().set_price()

        if self.discount:
            self.variant_payload['compareAtPrice'] = self.price
            self.variant_payload['price'] = self.discount
        else:
            self.variant_payload['price'] = self.price

    def set_product_type(self):
        self.payload['productType'] = self.rule.product_type.value

    def set_ean_code(self):
        super().set_ean_code()
        self.variant_payload['barcode'] = self.ean_code if self.ean_code else ''

    def build_payload(self):
        super().build_payload()
        self.set_sku()
        self.set_price()
        self.set_active()
        self.set_sku()
        self.set_allow_backorder()
        self.set_product_type()
        self.set_ean_code()

    def customize_payload(self):
        self.set_vendor()

        self.payload['metafields'] = self.metafields
        self.payload['tags'] = self.tags

        print('-------------------------------------------------- RESYNC 1')

    def get_saleschannel_remote_object(self, sku):
        gql = self.api.GraphQL()
        query = """
        query getProductByVariantSku($sku: String!) {
          productVariants(first: 1, query: $sku) {
            edges {
              node {
                id
                title
                handle
                variants(first: 10) {
                  edges {
                    node {
                      id
                      sku
                      title
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {"sku": f"sku:{sku}"}

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        print('--------------------------------- DATA')
        print(data)

        product_edges = data.get("data", {}).get("products", {}).get("edges", [])

        if not product_edges:
            raise ValueError(f"No Shopify product found with variant SKU: {sku}")

        return product_edges[0]["node"]

    def perform_remote_action(self):

        if not self.is_variation:
            product_result = self._update_product()

        variant_result = self._update_product_variant_only()

        print('----------------------------------------------------------------- RESYNCED')

        return {
            "product": self.payload,
            "variant": self.variant_payload
        }

    def _update_product(self):
        gql = self.api.GraphQL()
        query = """
        mutation productUpdate($product: ProductUpdateInput!) {
          productUpdate(product: $product) {
            product {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        self.payload["id"] = self.remote_instance.remote_id

        variables = {
            "product": self.payload
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        print('----------------------------------- RETURN DATA 1')
        print(data)

        errors = data.get("data", {}).get("productUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productUpdate userErrors: {errors}")

        return data["data"]["productUpdate"]

    def _update_product_variant_only(self):
        gql = self.api.GraphQL()
        query = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product {
              id
            }
            productVariants {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        self.variant_payload['id'] = self.remote_instance.default_variant_id
        parent_id = (
            self.remote_parent_product.remote_id
            if self.is_variation else self.remote_instance.remote_id
        )

        variables = {
            "productId": parent_id,
            "variants": [self.variant_payload]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        print('----------------------------------- RETURN DATA')
        print(data)

        errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantsBulkUpdate userErrors: {errors}")

        return data["data"]["productVariantsBulkUpdate"]

    def process_content_translation(self, short_description, description, url_key, remote_language):
        # @TODO: Come back to this
        pass

    def process_single_property(self, product_property):
        def add_to_metafields(fac):
            self.metafields.append({
                "namespace": fac.namespace,
                "key": fac.key,
                "value": fac.value,
                "type": fac.metafield_type,
            })

            if fac.local_instance.property.add_to_filters:
                self.tags.append(fac.value)

        try:
            remote_property = self.remote_product_property_class.objects.get(
                local_instance=product_property,
                remote_product=self.remote_instance,
                sales_channel=self.sales_channel
            )

            # Run the update factory in get_value_only mode
            update_factory = ShopifyProductPropertyUpdateFactory(
                local_instance=product_property,
                sales_channel=self.sales_channel,
                remote_product=self.remote_instance,
                remote_instance=remote_property,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            update_factory.run()

            if remote_property.needs_update(update_factory.remote_value):
                remote_property.remote_value = update_factory.remote_value
                remote_property.save()
                self.remote_product_properties.append(remote_property)
                add_to_metafields(update_factory)
                return remote_property.id

        except self.remote_product_property_class.DoesNotExist:
            create_factory = ShopifyProductPropertyCreateFactory(
                local_instance=product_property,
                sales_channel=self.sales_channel,
                remote_product=self.remote_instance,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            create_factory.run()

            self.remote_product_properties.append(create_factory.remote_instance)
            add_to_metafields(create_factory)
            return create_factory.remote_instance.id

        return remote_property.id

    def get_medias(self):
        return MediaProductThrough.objects.filter(
            product=self.local_instance,
            media__type__in=[Media.IMAGE, Media.VIDEO]
        ).order_by('-is_main_image', 'sort_order')

    def create_image_assignment(self, media_through):
        """
        Builds the media payload (get_value_only) and appends it to self.medias.
        Does NOT send the mutation yet.
        """
        factory = self.remote_image_assign_create_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api,
            get_value_only=True
        )
        factory.run()
        media_payload = factory.remote_instance_data

        if not hasattr(self, 'medias'):
            self.medias = []

        self.medias.append(media_payload)

        # still return a fake remote_instance for consistency
        return factory.remote_instance

    def update_image_assignment(self, media_through, remote_image_assoc):
        """
        Same as create, but uses the update factory in get_value_only mode.
        """
        factory = self.remote_image_assign_update_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_instance=remote_image_assoc,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api,
            get_value_only=True
        )
        factory.run()
        media_payload = factory.remote_instance_data

        if not hasattr(self, 'medias'):
            self.medias = []

        self.medias.append(media_payload)

        return factory.remote_instance


class ShopifyProductCreateFactory(ShopifyProductSyncFactory, RemoteProductCreateFactory):
    remote_price_class = ShopifyPrice
    remote_product_content_class = ShopifyProductContent
    remote_product_eancode_class = ShopifyEanCode

    def assign_images(self):
        # this will try to create the images AFTER the product but we already created them inside the product call
        pass

    def final_process(self):
        self._assign_metafield_remote_ids()
        self._assign_image_remote_ids()

    def _assign_image_remote_ids(self):
        images = self.product_data.get("media", {}).get("edges", [])
        if not images:
            return

        # Build lookup: alt text → media ID
        image_lookup = {}
        for edge in images:
            node = edge.get("node", {})
            if node.get("mediaContentType") == "IMAGE":
                alt = node.get("alt")
                if alt:
                    image_lookup[alt] = node.get("id")

        image_assocs = ShopifyImageProductAssociation.objects.filter(
            remote_product=self.remote_instance
        ).select_related("local_instance__media")

        for assoc in image_assocs:
            alt_name = getattr(assoc.local_instance.media.image, 'name', None)
            remote_id = image_lookup.get(alt_name)
            if remote_id:
                assoc.remote_id = remote_id
                assoc.save(update_fields=["remote_id"])

    def _assign_metafield_remote_ids(self):
        metafields = self.product_data.get("metafields", {}).get("edges", [])
        if not metafields:
            return

        # Build lookup by key
        metafield_lookup = {
            node["key"]: node["id"]
            for edge in metafields
            if (node := edge.get("node"))
        }

        product_properties = ShopifyProductProperty.objects.filter(
            remote_product=self.remote_instance
        )

        for prop in product_properties:
            remote_id = metafield_lookup.get(prop.key)
            if remote_id:
                prop.remote_id = remote_id
                prop.save(update_fields=["remote_id"])

    def customize_payload(self):
        super().customize_payload()
        super().assign_images()

    def perform_remote_action(self):
        if self.is_variation:
            self._create_product_variant_only()
        else:
            self._create_full_product_with_default_variant()

        return {
            "product": self.payload,
            "variant": self.variant_payload
        }

    def _create_product_variant_only(self):
        gql = self.api.GraphQL()
        query = """
        mutation ProductVariantsCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkCreate(productId: $productId, variants: $variants) {
            productVariants {
              id
              title
              selectedOptions {
                name
                value
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
            "productId": self.parent_remote_product.remote_id,
            "variants": [self.variant_payload]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkCreate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Shopify productVariantsBulkCreate userErrors: {errors}")

        variants = data["data"]["productVariantsBulkCreate"]["productVariants"]
        if not variants:
            raise ShopifyGraphqlException("No variants returned from Shopify.")

        variant_id = variants[0]["id"]
        self.remote_instance.remote_id = variant_id
        self.remote_instance.default_variant_id = variant_id
        self.remote_instance.save()

        return variants[0]

    def _create_full_product_with_default_variant(self):
        gql = self.api.GraphQL()
        query = f"""
        {MEDIA_FRAGMENT}

        mutation productCreateWithMedia($product: ProductCreateInput!, $media: [CreateMediaInput!]) {{
          productCreate(product: $product, media: $media) {{
            product {{
              id
              title
              variants(first: 1) {{
                edges {{
                  node {{
                    id
                  }}
                }}
              }}
              media(first: {len(self.medias)}) {{
                edges {{
                  node {{
                    ...fieldsForMediaTypes
                  }}
                }}
              }}
              {get_metafields(len(self.metafields))}
            }}
            userErrors {{
              field
              message
            }}
          }}
        }}
        """

        variables = {
            "product": self.payload,
            "media": self.medias,
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        print('-------------------- RETURN DATA')
        import pprint
        pprint.pprint(data)

        errors = data.get("data", {}).get("productCreate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Shopify productCreate userErrors: {errors}")

        self.product_data = data["data"]["productCreate"]["product"]
        variant_node = self.product_data["variants"]["edges"][0]["node"]

        remote_id = self.product_data["id"]
        variant_id = variant_node["id"]

        self.remote_instance.remote_id = remote_id
        self.remote_instance.default_variant_id = variant_id
        self.remote_instance.save()

        print('---------------------- ???')
        if self.local_instance.type == Product.CONFIGURABLE:
            print('----------------- CREATE VARIATIONS')
            self.create_variations()
        else:
            print('--------------------- UPDATE VARIANT')
            self.initial_variant_updated(variant_id)

        return self.product_data

    def create_variations(self):
        pass

    def initial_variant_updated(self, variant_id):
        gql = self.api.GraphQL()
        query = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product {
              id
            }
            productVariants {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        self.variant_payload['id'] = variant_id
        variables = {
            "productId": self.remote_instance.remote_id,
            "variants": [self.variant_payload]
        }

        print('--------------- VARIANT PAYLOAD')
        print(self.variant_payload)

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Shopify productVariantsBulkUpdate userErrors: {errors}")

    def serialize_response(self, response):
        return response.to_dict()


class ShopifyProductUpdateFactory(ShopifyProductSyncFactory, RemoteProductUpdateFactory):
    fixing_identifier_class = ShopifyProductSyncFactory


class ShopifyProductDeleteFactory(GetShopifyApiMixin, RemoteProductDeleteFactory):
    remote_model_class = ShopifyProduct
    delete_remote_instance = True

    def delete_remote(self):
        gql = self.api.GraphQL()

        if self.remote_instance.is_variation:
            query = """
            mutation bulkDeleteProductVariants($productId: ID!, $variantsIds: [ID!]!) {
              productVariantsBulkDelete(productId: $productId, variantsIds: $variantsIds) {
                product {
                  id
                  title
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """

            variables = {
                "productId": self.remote_instance.remote_parent_product.remote_id,
                "variantsIds": [self.remote_instance.remote_id],
            }

            response = gql.execute(query, variables=variables)
            data = json.loads(response)

            errors = data.get("data", {}).get("productVariantsBulkDelete", {}).get("userErrors", [])
            if errors:
                raise ShopifyGraphqlException(f"productVariantsBulkDelete userErrors: {errors}")

            return data

        else:
            query = """
            mutation deleteProduct($input: ProductDeleteInput!) {
              productDelete(input: $input) {
                deletedProductId
                userErrors {
                  field
                  message
                }
              }
            }
            """

            variables = {
                "input": {
                    "id": self.remote_instance.remote_id
                }
            }

            response = gql.execute(query, variables=variables)
            data = json.loads(response)

            errors = data.get("data", {}).get("productDelete", {}).get("userErrors", [])
            if errors:
                raise ShopifyGraphqlException(f"productDelete userErrors: {errors}")

            return data

    def serialize_response(self, response):
        return response
