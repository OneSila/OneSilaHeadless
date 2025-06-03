import datetime
import json
from decimal import Decimal

from mkdocs.config.config_options import Optional

from core.helpers import clean_json_data
from imports_exports.factories.imports import ImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportPropertyInstance
from products.models import Product
from properties.models import Property
from sales_channels.integrations.shopify.constants import MEDIA_FRAGMENT, DEFAULT_METAFIELD_NAMESPACE, SHOPIFY_TAGS
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyProduct, ShopifyEanCode, ShopifyProductProperty, \
    ShopifyProductContent, ShopifyImageProductAssociation, ShopifyPrice
from sales_channels.models import ImportProduct, SalesChannelViewAssign
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)


class ShopifyImportProcessor(ImportMixin, GetShopifyApiMixin):
    import_properties = True
    import_select_values = True
    import_rules = True
    import_products = True

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)

        self.sales_channel = sales_channel
        self.initial_sales_channel_status = sales_channel.active
        self.api = self.get_api()

    def prepare_import_process(self):

        # during the import this needs to stay false to prevent trying to create the mirror models because
        # we create them manually
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

        property_tag_data = {
            "name": "Shopify Tags",
            "internal_name": SHOPIFY_TAGS,
            "type": Property.TYPES.MULTISELECT,
            "is_public_information": False,
            "add_to_filters": False,
        }

        import_instance = ImportPropertyInstance(property_tag_data, self.import_process)
        import_instance.process()

        self.tags_property = import_instance.instance

    def get_total_instances(self):

        gql = self.api.GraphQL()
        query = """
        {
        productsCount {
            count
          }
        }
        """

        response = gql.execute(query)
        data = json.loads(response)

        return data["data"]["productsCount"]["count"]

    def get_properties_data(self):
        return []

    def get_select_values_data(self):
        return []

    def get_rules_data(self):
        return []

    def repair_remote_sku_if_needed(self, product, remote_product):
        local_sku = product.sku

        if not remote_product.default_variant_id or not local_sku:
            return

        if remote_product.is_variation:
            parent = remote_product.remote_parent_product

            if not parent or not parent.remote_id:
                return

            product_id = parent.remote_id
        else:
            if not remote_product.remote_id:
                return

            product_id = remote_product.remote_id

        gql = self.api.GraphQL()

        mutation = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product {
              id
            }
            productVariants {
              id
              sku
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {
            "productId": product_id,
            "variants": [
                {
                    "id": remote_product.default_variant_id,
                    "inventoryItem": {"sku": local_sku}
                }
            ]
        }

        response = gql.execute(mutation, variables=variables)
        data = json.loads(response)

        user_errors = data.get("data", {}).get("productVariantsBulkUpdate", {}).get("userErrors", [])
        if user_errors:
            logger.warning(f"Failed to repair SKU for {remote_product.remote_id}: {user_errors}")
            return

        logger.info(f"Repaired remote_sku for product {remote_product.remote_id} using default_variant_id")
        return local_sku

    def create_log_instance(self, import_instance: ImportProductInstance, structured_data: dict):

        log_instance = ImportProduct.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            import_process=self.import_process,
            remote_product=import_instance.remote_instance,
            raw_data=clean_json_data(import_instance.data),
            structured_data=clean_json_data(structured_data),
            successfully_imported=True
        )

        log_instance.content_type = ContentType.objects.get_for_model(import_instance.instance)
        log_instance.object_id = import_instance.instance.pk

    def handle_ean_code(self, import_instance: ImportProductInstance):

        shopify_ean_code, _ = ShopifyEanCode.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )

        if hasattr(import_instance, 'ean_code') and import_instance.ean_code:
            if shopify_ean_code.ean_code != import_instance.ean_code:
                shopify_ean_code.ean_code = import_instance.ean_code
                shopify_ean_code.save()

    def handle_attributes(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'attributes'):
            product_properties = import_instance.product_property_instances
            remote_product = import_instance.remote_instance
            mirror_map = import_instance.data.get('__mirror_product_properties_map', {})

            for product_property in product_properties:
                mirror_data = mirror_map.get(product_property.property.id)
                if not mirror_data:
                    continue

                key = mirror_data["key"]
                namespace = mirror_data.get("namespace", DEFAULT_METAFIELD_NAMESPACE)
                value = mirror_data["value"]
                remote_id = mirror_data.get("remote_id")

                remote_product_property, _ = ShopifyProductProperty.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=product_property,
                    remote_product=remote_product,
                )

                # Save value and Shopify metafield ID
                updated = False

                if not remote_product_property.key:
                    remote_product_property.key = key
                    updated = True

                if not remote_product_property.namespace:
                    remote_product_property.namespace = namespace
                    updated = True

                if not remote_product_property.remote_value:
                    remote_product_property.remote_value = value
                    updated = True

                if remote_id and not remote_product_property.remote_id:
                    remote_product_property.remote_id = remote_id
                    updated = True

                if updated:
                    remote_product_property.save()

    def handle_prices(self, import_instance: ImportProductInstance):
        if not hasattr(import_instance, 'prices'):
            return

        remote_product = import_instance.remote_instance

        shopify_price, _ = ShopifyPrice.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )

        price_data = {}

        for price_entry in import_instance.prices:
            currency = price_entry.get("currency")
            price = price_entry.get("price")
            rrp = price_entry.get("rrp")

            data = {}
            if rrp is not None:
                data["price"] = float(rrp)
            if price is not None:
                data["discount_price"] = float(price)

            if data:
                price_data[currency] = data

        if price_data:
            shopify_price.price_data = price_data
            shopify_price.save()

    def handle_translations(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'translations'):
            ShopifyProductContent.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
            )

    def handle_images(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'images'):
            remote_id_map = import_instance.data.get('__image_index_to_remote_id', {})

            for index, image_ass in enumerate(import_instance.images_associations_instances):
                image_association, _ = ShopifyImageProductAssociation.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=image_ass,
                    remote_product=import_instance.remote_instance,
                )

                remote_id = remote_id_map.get(str(index))
                if remote_id and not image_association.remote_id:
                    image_association.remote_id = remote_id
                    image_association.save()

    def handle_variations(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'variations'):
            variation_id_map = import_instance.data.get('__variation_sku_to_id_map', {})
            remote_product = import_instance.remote_instance
            variations = import_instance.variations_products_instances

            for index, product in enumerate(variations):
                info_map = variation_id_map.get(str(index), {})  # Use string key to match original map
                remote_id = info_map.get('id')
                remote_sku = info_map.get('sku')

                if remote_id:
                    shopify_product, _ = ShopifyProduct.objects.get_or_create(
                        multi_tenant_company=self.import_process.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        local_instance=product,
                        is_variation=True,
                    )

                    shopify_product.remote_id = remote_id
                    shopify_product.remote_parent_product = remote_product

                    if not remote_sku:
                        shopify_product.remote_sku = self.repair_remote_sku_if_needed(product, shopify_product)

                    shopify_product.save()

            # Handle configurator (same logic)
            from sales_channels.models.products import RemoteProductConfigurator
            if hasattr(remote_product, 'configurator'):
                configurator = remote_product.configurator
                configurator.update_if_needed(rule=import_instance.rule, variations=variations, send_sync_signal=False)
            else:
                RemoteProductConfigurator.objects.create_from_remote_product(
                    remote_product=remote_product,
                    rule=import_instance.rule,
                    variations=variations,
                )

    def handle_sales_channels_views(self, import_instance: ImportProductInstance, product: dict):

        sales_channel_view = self.sales_channel.saleschannelview_set.filter(
            multi_tenant_company=self.import_process.multi_tenant_company
        ).first()

        if not sales_channel_view:
            return

        SalesChannelViewAssign.objects.get_or_create(
            product=import_instance.instance,
            sales_channel_view=sales_channel_view,
            multi_tenant_company=self.import_process.multi_tenant_company,
            remote_product=import_instance.remote_instance,
            sales_channel=self.sales_channel,
        )

    def update_remote_product(self, import_instance: ImportProductInstance, product: dict, is_variation: bool):
        remote_product = import_instance.remote_instance

        remote_id = product.get("id")
        if not remote_product.remote_id and remote_id:
            remote_product.remote_id = remote_id

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation

        if is_variation:
            remote_product.default_variant_id = remote_id
            remote_product.remote_sku = product.get("sku") or None
        else:
            variants = product.get("variants", {}).get("edges", [])
            if len(variants) == 1:
                variant_node = variants[0]["node"]
                default_variant_id = variant_node.get("id")
                if default_variant_id:
                    remote_product.default_variant_id = default_variant_id

                remote_sku = variant_node.get("sku") or None

                if remote_sku:
                    remote_product.remote_sku = remote_sku
                else:
                    remote_product.remote_sku = self.repair_remote_sku_if_needed(import_instance.instance, import_instance.remote_instance)

        remote_product.save()

    def get_product_translations(self, product: dict, variation_name: str = None):

        name = product.get("title")
        if variation_name is not None:
            name = variation_name

        return [{
            "name": name,
            "description": product.get("descriptionHtml"),
            "url_key": product.get("handle"),
            # "short_description": None,  # Not available from Shopify, skipping for now
        }]

    def get_product_images(self, product: dict):
        images = []
        image_id_map = {}

        media_edges = product.get("media", {}).get("edges", [])

        for index, edge in enumerate(media_edges):
            node = edge.get("node")
            if not isinstance(node, dict):
                continue

            media_type = node.get("mediaContentType")

            if media_type not in ["IMAGE", "EXTERNAL_VIDEO"]:
                continue

            url = None

            if media_type == "IMAGE":
                image_obj = node.get("image") or {}
                original_source = node.get("originalSource") or {}
                preview_image = (node.get("preview") or {}).get("image") or {}

                url = (
                    image_obj.get("url") or
                    original_source.get("url") or
                    preview_image.get("url")
                )

            elif media_type == "EXTERNAL_VIDEO":
                preview_image = (node.get("preview") or {}).get("image") or {}
                original_source = node.get("originalSource") or {}

                url = (
                    preview_image.get("url") or
                    original_source.get("url")
                )

            if not url:
                continue

            image_data = {
                "image_url": url,
                "sort_order": index
            }

            if index == 0:
                image_data["is_main_image"] = True

            images.append(image_data)
            image_id_map[str(index)] = node.get("id")

        return images, image_id_map

    def get_or_create_property(self, name: str, internal_type: str):
        # Check if property already exists
        prop = Property.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            internal_name=name
        ).first()

        if not prop:
            data = {
                "name": name.replace("_", " ").title(),
                "internal_name": name,
                "type": internal_type,
                "is_public_information": True,
                "add_to_filters": False,
                "has_image": False
            }
            import_instance = ImportPropertyInstance(data, self.import_process)
            import_instance.process()
            prop = import_instance.instance

        return prop

    def get_product_attributes(self, product: dict, product_type: str):
        attributes = []
        configurator_select_values = []
        mirror_map = {}

        metafield_edges = product.get("metafields", {}).get("edges", [])
        selected_options = product.get("selectedOptions", [])

        for edge in metafield_edges:
            node = edge["node"]
            key = node["key"]
            ns = node["namespace"]
            value = node["value"]
            type_ = node["type"]
            metafield_id = node["id"]

            normalized_key = key.lower().replace("-", "_")
            internal_type = self.shopify_type_to_internal(type_)

            if not internal_type:
                continue

            if internal_type == Property.TYPES.DATE:
                try:
                    parsed = datetime.strptime(value, "%Y-%m-%d")
                    value = parsed.strftime("%Y-%m-%d 00:00:00")
                except Exception as e:
                    logger.debug(f"Skipping invalid DATE metafield {key}: {value} — {e}")
                    continue

            elif internal_type == Property.TYPES.DATETIME:
                try:
                    value = value.rstrip("Z")
                    parsed = datetime.fromisoformat(value)
                    value = parsed.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.debug(f"Skipping invalid DATETIME metafield {key}: {value} — {e}")
                    continue

            prop = self.get_or_create_property(
                name=normalized_key,
                internal_type=internal_type
            )

            attributes.append({
                "property": prop,
                "value": value,
            })

            mirror_map[prop.id] = {
                "key": key,
                "namespace": ns,
                "value": value,
                "remote_id": metafield_id,
            }

        brand_attr = self.sales_channel.vendor_property
        vendor_value = product.get("vendor", None)
        if brand_attr and vendor_value is not None:
            attributes.append({
                "property": brand_attr,
                "value": vendor_value,
            })

            mirror_map[brand_attr.id] = {
                "key": "vendor",
                "namespace": DEFAULT_METAFIELD_NAMESPACE,
                "value": vendor_value,
                "remote_id": None,
            }

        if self.tags_property:
            attributes.append({
                "property": self.tags_property,
                "value": product.get("tags"),
            })

            mirror_map[self.tags_property.id] = {
                "key": "tags",
                "namespace": DEFAULT_METAFIELD_NAMESPACE,
                "value": product.get("tags"),
                "remote_id": None,
            }

        # Step 2: selectedOptions → configurator_select_values
        if selected_options:
            seen_keys = set()
            for option in selected_options:
                key = option.get("name")
                value = option.get("value")

                if key == "Title" and (not value or value.strip().lower() == "default title"):
                    continue

                normalized_key = key.lower().replace(" ", "_").replace("-", "_")

                if normalized_key in seen_keys:
                    continue

                seen_keys.add(normalized_key)

                prop = self.get_or_create_property(
                    name=normalized_key,
                    internal_type=Property.TYPES.SELECT
                )

                configurator_select_values.append({
                    "property": prop,
                    "value": value,
                })

                attributes.append({
                    "property": prop,
                    "value": value,
                })

                mirror_map[prop.id] = {
                    "key": normalized_key,
                    "namespace": DEFAULT_METAFIELD_NAMESPACE,
                    "value": value,
                    "remote_id": None,
                }

        return attributes, configurator_select_values or [], mirror_map

    def shopify_type_to_internal(self, shopify_type):
        mapping = {
            'number_integer': Property.TYPES.INT,
            'number_decimal': Property.TYPES.FLOAT,
            'single_line_text_field': Property.TYPES.SELECT,
            'multi_line_text_field': Property.TYPES.DESCRIPTION,
            'boolean': Property.TYPES.BOOLEAN,
            'date': Property.TYPES.DATE,
            'date_time': Property.TYPES.DATETIME,
            'json_string': Property.TYPES.MULTISELECT,
        }
        return mapping.get(shopify_type, Property.TYPES.TEXT)

    def get_product_prices(self, product: dict):
        """
        Returns a list with one price dict based on:
        - The product itself (if it's a variant and has price fields)
        - OR the first variant (if only one exists)
        - OR [] if multiple variants and price cannot be inferred
        """
        prices = []

        price = product.get("price")
        compare_at_price = product.get("compareAtPrice")

        if price is not None or compare_at_price is not None:
            price_entry = {}
            if price is not None:
                price_entry["price"] = price
            if compare_at_price is not None:
                price_entry["rrp"] = compare_at_price
            prices.append(price_entry)
            return prices

        variants = product.get("variants", {}).get("edges", [])
        if len(variants) == 1:
            variant = variants[0]["node"]
            price = variant.get("price")
            compare_at_price = variant.get("compareAtPrice")

            if price is not None or compare_at_price is not None:
                price_entry = {}
                if price is not None:
                    price_entry["price"] = price
                if compare_at_price is not None:
                    price_entry["rrp"] = compare_at_price
                prices.append(price_entry)

        return prices

    def get_product_variations(self, product: dict, parent_active: bool = True, configurable_attributes: list | None = None, configurable_configurator_select_values: Optional[dict] = None):
        """
        For CONFIGURABLE products.

        - Builds variations list based on the variant edges.
        - Constructs an index → Shopify variant ID + SKU map.

        Returns:
            - List of variation_data dicts.
            - Index-to-ID mapping.
        """
        variations = []
        index_to_id_map = {}
        parent_name = product.get("title", "").strip()
        product_type = product.get("productType")
        variant_edges = product.get("variants", {}).get("edges", [])

        for idx, edge in enumerate(variant_edges):
            node = edge["node"]
            sku = node.get("sku") or None
            shopify_id = node.get("id")
            selected_options = node.get("selectedOptions", [])

            option_labels = [
                opt["value"].strip()
                for opt in selected_options
                if opt.get("name") != "Title"
            ]

            if option_labels:
                name = f"{parent_name} – {' x '.join(option_labels)}"
            else:
                name = parent_name

            product = self.get_product_data(
                node,
                is_variation=True,
                variation_name=name,
                parent_product_type=product_type,
                configurable_attributes=configurable_attributes,
                configurable_configurator_select_values=configurable_configurator_select_values)

            variation_data = {
                "name": name,
                "type": Product.SIMPLE,
                "active": parent_active,
            }

            if sku:
                variation_data["sku"] = sku
            else:
                variation_data["sku"] = product.sku

            variations.append({"variation_data": variation_data})
            index_to_id_map[str(idx)] = {
                "id": shopify_id,
                "sku": sku,
            }

        return variations, index_to_id_map

    def get_product_data(self, product: dict, is_variation: bool = False, variation_name: str = None, parent_product_type: str = None, configurable_attributes: list | None = None, configurable_configurator_select_values: Optional[dict] = None):
        variants = product.get("variants", {}).get("edges", [])
        is_configurable = len(variants) > 1
        product_type = Product.CONFIGURABLE if is_configurable else Product.SIMPLE

        active = product.get("status") == "ACTIVE"
        structured_data = {
            "name": product.get("title"),
            "type": product_type,
            "active": active,
        }

        rule_product_type = product.get("productType") if parent_product_type is None else parent_product_type
        if rule_product_type:
            structured_data["product_type"] = rule_product_type

        if 'sku' in product:
            sku = product.get("sku")
            inventory_policy = product.get("inventoryPolicy")

            structured_data["allow_backorder"] = inventory_policy == "CONTINUE"
            structured_data["ean_code"] = product.get("barcode")

            if sku:
                structured_data["sku"] = sku

        else:

            if product_type == Product.SIMPLE and variants:
                first_variant = variants[0]["node"]

                sku = first_variant.get("sku")

                if sku:
                    structured_data["sku"] = sku

                inventory_policy = first_variant.get("inventoryPolicy")
                structured_data["allow_backorder"] = inventory_policy == "CONTINUE"
                structured_data["ean_code"] = first_variant.get("barcode")

        structured_data['translations'] = self.get_product_translations(product, variation_name)
        structured_data['images'], structured_data['__image_index_to_remote_id'] = self.get_product_images(product)

        if product_type == Product.SIMPLE:
            structured_data['prices'] = self.get_product_prices(product)

        attributes, configurator_select_values, mirror_product_properties_map = self.get_product_attributes(product, product_type=product_type)

        if product_type == Product.SIMPLE:
            structured_data['attributes'] = attributes
            structured_data['__mirror_product_properties_map'] = mirror_product_properties_map
            structured_data['configurator_select_values'] = configurator_select_values

        if product_type == Product.CONFIGURABLE:
            structured_data['configurator_select_values'] = configurator_select_values

        if is_variation:

            if configurable_attributes:

                if 'attributes' in structured_data:
                    structured_data['attributes'].extend(configurable_attributes)
                else:
                    structured_data['attributes'] = configurable_attributes

            if configurable_configurator_select_values:
                if '__mirror_product_properties_map' in structured_data:
                    structured_data['__mirror_product_properties_map'].update(configurable_configurator_select_values)
                else:
                    structured_data['__mirror_product_properties_map'] = configurable_configurator_select_values

        if product_type == Product.CONFIGURABLE:

            structured_data['variations'], structured_data['__variation_sku_to_id_map'] = self.get_product_variations(
                product,
                parent_active=active,
                configurable_attributes=attributes,
                configurable_configurator_select_values=configurable_configurator_select_values)

        remote_instance = ShopifyProduct.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=product.get("id")
        ).first()

        instance = None
        if remote_instance:
            instance = remote_instance.local_instance

        import_instance = ImportProductInstance(
            data=structured_data,
            import_process=self.import_process,
            instance=instance
        )

        import_instance.prepare_mirror_model_class(
            mirror_model_class=ShopifyProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={"remote_id": product["id"], 'is_variation': is_variation}
        )

        import_instance.process()

        self.update_remote_product(import_instance, product, is_variation)
        self.create_log_instance(import_instance, structured_data)
        self.handle_ean_code(import_instance)
        self.handle_attributes(import_instance)
        self.handle_translations(import_instance)
        self.handle_prices(import_instance)
        self.handle_images(import_instance)
        self.handle_variations(import_instance)

        if not is_variation:
            self.handle_sales_channels_views(import_instance, product)

        return import_instance.instance

    def import_products_process(self):
        gql = self.api.GraphQL()
        has_next_page = True
        after_cursor = None
        per_page = 50

        while has_next_page:
            query = f"""
            {MEDIA_FRAGMENT}

            query Products($first: Int, $after: String) {{
              products(first: $first, after: $after) {{
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
                edges {{
                  node {{
                    id
                    title
                    handle
                    status
                    productType
                    tags
                    vendor
                    descriptionHtml
                    variants(first: 100) {{
                      edges {{
                        node {{
                          id
                          sku
                          barcode
                          price
                          compareAtPrice
                          inventoryPolicy
                          inventoryItem {{
                           sku
                           tracked
                           }}
                           metafields(first: 20) {{
                              edges {{
                                node {{
                                  id
                                  namespace
                                  key
                                  value
                                  type
                                }}
                              }}
                            }}
                          selectedOptions {{
                            name
                            value
                          }}
                        }}
                      }}
                    }}
                    media(first: 20) {{
                        edges {{
                          node {{
                            ...fieldsForMediaTypes
                          }}
                        }}
                      }}
                    metafields(first: 20) {{
                      edges {{
                        node {{
                          id
                          namespace
                          key
                          value
                          type
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """

            variables = {
                "first": per_page,
                "after": after_cursor
            }

            response = gql.execute(query, variables=variables)
            data = json.loads(response)

            # Parse pagination data
            page_info = data["data"]["products"]["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            after_cursor = page_info["endCursor"]

            # Process products
            for edge in data["data"]["products"]["edges"]:
                product = edge["node"]

                self.get_product_data(product)
                self.update_percentage()

    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save()
