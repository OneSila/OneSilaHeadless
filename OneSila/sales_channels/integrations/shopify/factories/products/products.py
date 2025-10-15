import copy
import json

from media.models import MediaProductThrough, Media
from products.models import Product
from properties.models import ProductProperty, Property
from sales_channels.exceptions import SwitchedToCreateException, SwitchedToSyncException
from sales_channels.factories.products.products import (
    RemoteProductSyncFactory,
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
)
from sales_channels.integrations.shopify.constants import ACTIVE_STATUS, NON_ACTIVE_STATUS, \
    ALLOW_BACKORDER_CONTINUE, ALLOW_BACKORDER_DENY, MEDIA_FRAGMENT, get_metafields, SHOPIFY_TAGS
from sales_channels.integrations.shopify.exceptions import ShopifyGraphqlException
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyProductProperty, ShopifySalesChannelView
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
    sales_channel_allow_duplicate_sku = True

    # Sub-factories for images, metafields, EAN, etc.
    remote_image_assign_create_factory = ShopifyMediaProductThroughCreateFactory
    remote_image_assign_update_factory = ShopifyMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = ShopifyMediaProductThroughDeleteFactory

    remote_product_property_class = ShopifyProductProperty
    remote_product_property_create_factory = ShopifyProductPropertyCreateFactory
    remote_product_property_update_factory = ShopifyProductPropertyUpdateFactory
    remote_product_property_delete_factory = ShopifyProductPropertyDeleteFactory

    remote_eancode_update_factory = ShopifyEanCodeUpdateFactory

    sync_product_factory = property(lambda self: ShopifyProductSyncFactory)
    create_product_factory = property(lambda self: ShopifyProductCreateFactory)
    delete_product_factory = property(lambda self: ShopifyProductDeleteFactory)
    add_variation_factory = property(lambda self: ShopifyProductSyncFactory)

    # Local field → Shopify REST API field mapping
    field_mapping = {
        'name': 'title',
        'url_key': 'handle',
        'description': 'descriptionHtml',
        'content': 'content',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.variant_payload = {
            'inventoryItem': {}
        }
        self.metafields = []
        self.tags = []
        self.medias = []

    def set_sku(self):
        self.sku = self.local_instance.sku
        self.variant_payload['inventoryItem']['sku'] = self.local_instance.sku
        self.variant_payload['inventoryItem']['tracked'] = True

    def set_variation_sku(self):
        self.set_sku()

    def get_variation_sku(self):
        return self.local_instance.sku

    def set_active(self):
        self.payload['status'] = ACTIVE_STATUS if self.local_instance.active else NON_ACTIVE_STATUS

    def set_allow_backorder(self):
        self.variant_payload['inventoryPolicy'] = ALLOW_BACKORDER_CONTINUE if self.local_instance.allow_backorder else ALLOW_BACKORDER_DENY

    def set_vendor(self):
        if self.sales_channel.vendor_property:

            # the update method does not fetch the product_properties
            if not hasattr(self, 'product_properties'):
                self.set_product_properties()

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

    def set_tags(self):
        tags_product_property = ProductProperty.objects.filter(
            product=self.local_instance,
            property__internal_name=SHOPIFY_TAGS
        ).first()

        tags = []
        if tags_product_property:
            for select_value in tags_product_property.value_multi_select.all():
                v = select_value.value
                tags.append(v)

        self.payload['tags'] = tags

    def build_payload(self):
        self.set_sku()
        super().build_payload()
        self.set_price()
        self.set_active()
        self.set_allow_backorder()
        self.set_product_type()
        self.set_ean_code()

    def customize_payload(self):
        self.set_vendor()
        self.set_tags()

        if self.is_variation:
            self.variant_payload['metafields'] = self.metafields
        else:
            self.payload['metafields'] = self.metafields

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

        product_edges = data.get("data", {}).get("products", {}).get("edges", [])

        if not product_edges:
            raise ValueError(f"No Shopify product found with variant SKU: {sku}")

        return product_edges[0]["node"]

    def perform_remote_action(self):

        if not self.is_variation:
            product_result = self._update_product()

        if self.local_type != Product.CONFIGURABLE:
            # update the default variant fields if not configurable
            variant_result = self._update_product_variant_only()

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

        errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantsBulkUpdate userErrors: {errors}")

        return data["data"]["productVariantsBulkUpdate"]

    def process_content_translation(self, short_description, description, url_key, remote_language):
        # @TODO: Come back to this
        pass

    def process_single_property(self, product_property, *, skip_remote_mirror=False):
        def add_to_metafields(fac):
            self.metafields.append({
                "namespace": fac.namespace,
                "key": fac.key,
                "value": fac.value,
                "type": fac.metafield_type,
            })

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
        return (
            MediaProductThrough.objects.get_product_images(
                product=self.local_instance,
                sales_channel=self.sales_channel,
            )
            .filter(media__type__in=[Media.IMAGE, Media.VIDEO])
            .order_by('-is_main_image', 'sort_order')
        )

    def create_image_assignment(self, media_through):
        """
        Builds the media payload (get_value_only) and appends it to self.medias.
        Does NOT send the mutation yet.
        """
        if self.is_variation:
            # @TODO: For now we skip
            return None

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

    def add_variation_to_parent(self):
        pass

    def run_for_payload(self):

        # we run sync but don't do any remote action so it can be used for bulk operations
        if not self.preflight_check():
            logger.debug(f"Preflight check failed for {self.sales_channel}.")
            return

        self.set_api()
        log_identifier, fixing_identifier = self.get_identifiers()

        self.set_type()
        try:
            self.initialize_remote_product()
            self.set_remote_product_for_logging()

            if self.local_type == Product.CONFIGURABLE:
                self.get_variations()

            self.set_local_assigns()
            self.set_rule()
            self.build_payload()
            self.set_product_properties()
            self.process_product_properties()

            if self.local_type == Product.CONFIGURABLE:
                self.set_remote_configurator()

            self.customize_payload()

            self.final_process()
            self.log_action(self.action_log, {}, self.payload, log_identifier)

        except SwitchedToCreateException as stc:
            logger.debug(stc)
            if self.is_switched:
                raise stc
            self.is_switched = True
            self.run_create_flow()

        except SwitchedToSyncException as sts:
            logger.debug(sts)
            if self.is_switched:
                raise sts
            self.is_switched = True
            self.run_sync_flow()

        except Exception as e:
            self.log_error(e, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            self.finalize_progress()


class ShopifyProductCreateFactory(ShopifyProductSyncFactory, RemoteProductCreateFactory):
    remote_price_class = ShopifyPrice
    remote_product_content_class = ShopifyProductContent
    remote_product_eancode_class = ShopifyEanCode
    variations_payload = []
    sku_variations_map = {}

    def assign_images(self):
        # this will try to create the images AFTER the product but we already created them inside the product call
        pass

    def final_process(self):

        if not self.is_variation:
            # we only publish the main product
            # the _assign_metafield_remote_ids and _assign_image_remote_ids for variation happen in bulk method
            self._assign_metafield_remote_ids()
            self._assign_image_remote_ids()
            self._publish_product()

    def _apply_starting_stock(self):

        # this is temporary not applied because it is breaking the inventory (sku / backorder) integration
        if not getattr(self, "is_create", False):
            return

        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock is None:
            return

        self.variant_payload['inventoryQuantity'] = starting_stock

    def _publish_product(self):
        publication_ids = ShopifySalesChannelView.objects.filter(sales_channel=self.sales_channel).values_list('publication_id', flat=True).distinct()

        if not publication_ids:
            return

        gql = self.api.GraphQL()

        query = """
        mutation productPublish($input: ProductPublishInput!) {
          productPublish(input: $input) {
            product {
              id
            }
            productPublications {
              channel {
                id
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
            "input": {
                "id": self.remote_instance.remote_id,
                "productPublications": [
                    {
                        "publicationId": pub_id
                    } for pub_id in publication_ids
                ]
            }
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productPublish", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productPublish userErrors: {errors}")

    def set_product_data_and_remote_product(self, product_data, remote_product):

        if product_data is None:
            product_data = self.product_data

        if remote_product is None:
            remote_product = self.remote_instance

        return product_data, remote_product

    def _assign_image_remote_ids(self, product_data=None, remote_product=None):

        product_data, remote_product = self.set_product_data_and_remote_product(product_data, remote_product)
        images = product_data.get("media", {}).get("edges", [])
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
            remote_product=remote_product
        ).select_related("local_instance__media")

        for assoc in image_assocs:
            alt_name = getattr(assoc.local_instance.media.image, 'name', None)
            remote_id = image_lookup.get(alt_name)
            if remote_id:
                assoc.remote_id = remote_id
                assoc.save(update_fields=["remote_id"])

    def _assign_metafield_remote_ids(self, product_data=None, remote_product=None):

        product_data, remote_product = self.set_product_data_and_remote_product(product_data, remote_product)
        metafields = product_data.get("metafields", {}).get("edges", [])
        if not metafields:
            return

        # Build lookup by key
        metafield_lookup = {
            node["key"]: node["id"]
            for edge in metafields
            if (node := edge.get("node"))
        }

        product_properties = ShopifyProductProperty.objects.filter(
            remote_product=remote_product
        )

        for prop in product_properties:
            remote_id = metafield_lookup.get(prop.key)
            if remote_id:
                prop.remote_id = remote_id
                prop.save(update_fields=["remote_id"])

    def customize_payload(self):
        super().customize_payload()
        super().assign_images()

        if self.local_instance.type == Product.CONFIGURABLE:
            self.payload['productOptions'] = self.get_product_options()
        else:
            if self.is_variation:
                self.variant_payload['optionValues'] = self.get_option_values()

    def get_product_options(self):
        from collections import defaultdict

        options = defaultdict(set)

        for variation in self.variations:
            product_properties = ProductProperty.objects.filter(
                property_id__in=self.configurator.properties.values_list('id', flat=True),
                product=variation
            ).select_related('property', 'value_select')

            for prop in product_properties:
                prop_name = prop.property.name
                value = prop.value_select.value
                if value:
                    options[prop_name].add(value)

        product_options = [
            {
                "name": name,
                "values": [{"name": value} for value in sorted(values)]
            }
            for name, values in options.items()
        ]

        return product_options

    def get_option_values(self):
        props_qs = self.product_properties.filter(
            property_id__in=self.remote_parent_product.configurator.properties.values_list('id', flat=True)
        ).select_related('property', 'value_select')

        values = []
        for prop in props_qs:
            value = prop.value_select.value
            if value:
                values.append({"name": value, "optionName": prop.property.name})

        return values

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
        query = f"""
        mutation ProductVariantsCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {{
          productVariantsBulkCreate(productId: $productId, variants: $variants) {{
            productVariants {{
              id
              title
              {get_metafields(len(self.metafields))}
              selectedOptions {{
                name
                value
              }}
            }}
            userErrors {{
              field
              message
            }}
          }}
        }}
        """

        variables = {
            "productId": self.remote_parent_product.remote_id,
            "variants": [self.variant_payload],
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkCreate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Shopify productVariantsBulkCreate userErrors: {errors}")

        variants = data["data"]["productVariantsBulkCreate"]["productVariants"]
        if not variants:
            raise ShopifyGraphqlException("No variants returned from Shopify.")

        self.product_data = variants[0]
        variant_id = self.product_data["id"]
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
              options {{
                  id
                  name
                  position
                  optionValues {{
                    id
                    name
                    hasVariants
                  }}
                }}
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

        errors = data.get("data", {}).get("productCreate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Shopify productCreate userErrors: {errors}")

        if "data" not in data:
            raise ShopifyGraphqlException(f"GraphQL error: {json.dumps(data, indent=2)}")

        self.product_data = data["data"]["productCreate"]["product"]
        variant_node = self.product_data["variants"]["edges"][0]["node"]

        remote_id = self.product_data["id"]
        variant_id = variant_node["id"]

        self.remote_instance.remote_id = remote_id
        self.remote_instance.default_variant_id = variant_id
        self.remote_instance.save()

        if self.local_instance.type != Product.CONFIGURABLE:
            self.initial_variant_updated(variant_id)

        return self.product_data

    def create_variations(self):

        if not self.variations_payload:
            return

        gql = self.api.GraphQL()
        query = f"""
        {MEDIA_FRAGMENT}

        mutation ProductVariantsCreate(
            $productId: ID!,
            $variants: [ProductVariantsBulkInput!]!,
            $strategy: ProductVariantsBulkCreateStrategy = REMOVE_STANDALONE_VARIANT
        ) {{
          productVariantsBulkCreate(
            productId: $productId,
            variants: $variants,
            strategy: $strategy
          ) {{
            productVariants {{
              id
              title
              sku
              selectedOptions {{
                name
                value
              }}
              media(first: {len(self.medias)}) {{
                edges {{
                  node {{
                    ...fieldsForMediaTypes
                  }}
                }}
              }}
              {get_metafields(25)}
            }}
            userErrors {{
              field
              message
            }}
          }}
        }}
        """

        variables = {
            "productId": self.remote_instance.remote_id,
            "variants": self.variations_payload,
            "strategy": "REMOVE_STANDALONE_VARIANT"
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkCreate", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"productVariantsBulkCreate (bulk) userErrors: {errors}")

        created_variants = data["data"]["productVariantsBulkCreate"]["productVariants"]

        # Assign remote_id + default_variant_id to each variation RemoteProduct
        for variant in created_variants:
            sku = variant.get("sku")
            remote_id = variant.get("id")

            if not sku or not remote_id:
                continue

            remote_variation = self.sku_variations_map.get(sku)

            if remote_variation:
                remote_variation.remote_id = remote_id
                remote_variation.default_variant_id = remote_id
                remote_variation.save(update_fields=["remote_id", "default_variant_id"])

            self._assign_image_remote_ids(variant, remote_variation)
            self._assign_metafield_remote_ids(variant, remote_variation)

    def create_or_update_children(self):
        super().create_or_update_children()
        self.create_variations()

        # self.delete_default_variant()

    def create_child(self, variation):
        factory = self.create_product_factory(
            sales_channel=self.sales_channel,
            local_instance=variation,
            parent_local_instance=self.local_instance,
            remote_parent_product=self.remote_instance,
            api=self.api,
        )
        factory.metafields = []
        factory.run_for_payload()
        remote_variation = factory.remote_instance

        self.variations_payload.append(copy.deepcopy(factory.variant_payload))
        self.sku_variations_map[factory.sku] = remote_variation
        return remote_variation

    def delete_default_variant(self):

        gql = self.api.GraphQL()
        query = """
        mutation deleteDefaultVariant($productId: ID!, $variantsIds: [ID!]!) {
          productVariantsBulkDelete(productId: $productId, variantsIds: $variantsIds) {
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

        variables = {
            "productId": self.remote_instance.remote_id,
            "variantsIds": [self.remote_instance.default_variant_id]
        }

        response = gql.execute(query, variables=variables)
        data = json.loads(response)

        errors = data.get("data", {}).get("productVariantsBulkDelete", {}).get("userErrors", [])
        if errors:
            raise ShopifyGraphqlException(f"Could not delete default variant: {errors}")

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
