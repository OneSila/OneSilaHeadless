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
    ShopifyProductContent
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

    # References to create/update/delete product factories
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
        self.variant_payload['barcode'] = self.ean_code

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

    def get_saleschannel_remote_object(self, sku):
        """
        Used by CreateFactory to detect existing remote product by handle/variants.
        Override if needed.
        """
        return self.api.Product.find(handle=sku)

    def process_content_translation(self, short_description, description, url_key, remote_language):
        # @TODO: Come back to this
        pass

    def process_single_property(self, product_property):
        print('-------------------------- AICI E BUBA!')
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

        print('------------------- PAYLOAD')
        print(media_payload)

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

        print('------------------- PAYLOAD 2')
        print(media_payload)

        if not hasattr(self, 'medias'):
            self.medias = []

        self.medias.append(media_payload)

        return factory.remote_instance


class ShopifyProductCreateFactory(ShopifyProductSyncFactory, RemoteProductCreateFactory):
    remote_price_class = ShopifyPrice
    remote_product_content_class = ShopifyProductContent
    remote_product_eancode_class = ShopifyEanCode

    def assign_images(self):
        pass
    def customize_payload(self):
        super().customize_payload()
        super().assign_images()

    def perform_remote_action(self):
        if self.is_variation:
            return self._create_product_variant_only()
        else:
            return self._create_full_product_with_default_variant()

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

        product_data = data["data"]["productCreate"]["product"]
        variant_node = product_data["variants"]["edges"][0]["node"]

        remote_id = product_data["id"]
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

        return product_data

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
              metafields(first: 2) {
                edges {
                  node {
                    namespace
                    key
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
    api_package_name = 'Product'
    api_method_name = 'update'

    def perform_remote_action(self):
        product = self.api.Product.find(self.remote_instance.remote_id)
        if not product:
            raise ValueError(f"No Shopify product found with id {self.remote_instance.remote_id}")

        # Apply top-level updates
        for field, val in self.payload.items():
            setattr(product, field, val)

        product.save()

        return product

    def serialize_response(self, response):
        return response.to_dict()


class ShopifyProductDeleteFactory(GetShopifyApiMixin, RemoteProductDeleteFactory):
    remote_model_class = ShopifyProduct
    delete_remote_instance = True

    def delete_remote(self):
        product = self.api.Product.find(self.remote_instance.remote_id)
        if not product:
            return True
        return product.destroy()
