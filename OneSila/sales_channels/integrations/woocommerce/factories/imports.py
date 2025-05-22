
import json
from decimal import Decimal
from core.helpers import clean_json_data
from sales_channels.factories.imports import SalesChannelImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportPropertyInstance
from products.models import Product
from properties.models import Property
from .exceptions import SanityCheckError
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, \
    WoocommerceEanCode, WoocommerceProductProperty, \
    WoocommerceProductContent, WoocommercePrice, \
    WoocommerceMediaThroughProduct
from sales_channels.models import ImportProduct, SalesChannelViewAssign
from django.contrib.contenttypes.models import ContentType

from imports_exports.factories.media import ImportImageInstance
from typing import Generator

import logging
logger = logging.getLogger(__name__)


class WoocommerceImportProcessor(SalesChannelImportMixin, GetWoocommerceAPIMixin):
    remote_imageproductassociation_class = WoocommerceMediaThroughProduct
    remote_price_class = WoocommercePrice
    remote_ean_code_class = WoocommerceEanCode

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, sales_channel, language)
        self.repair_sku_map = {}
        self.max_repair_batch_size = 250

    def get_total_instances(self):
        return len(self.api.get_products())

    def get_products_data(self):
        """
        Fetch products from the API and return all of them.
        """
        return self.api.get_products()

    def get_base_product_data(self, product_data) -> tuple[dict, bool]:
        """
        return a payload {} and is_variation bool that contains the root fields for the product data
        {
            "name": "T-Shirt Config",
            "sku": "TSHIRT-CONFIG-01",
            "type": "CONFIGURABLE",
            "product_type": "TShirt",
        }
        """
        # Note, no such thing as a product-type in woocommerce.
        ptype = product_data.get('type')

        if ptype == 'simple':
            local_type = Product.SIMPLE
            is_variation = False
        elif ptype == 'variable':
            local_type = Product.CONFIGURABLE
            is_variation = False
        elif ptype == 'vaiation':
            local_type = Product.SIMPLE
            is_variation = True
        else:
            raise NotImplementedError(f"Unknown woocommcerce product type: {ptype}")

        payload = {
            'name': product_data.get('name'),
            'sku': product_data.get('sku'),
        }

        return payload, is_variation

    def get_prices(self, product_data) -> dict:
        """
        get the price data
        { "price": 19.99,
        "currency": "GBP" }
        """
        currency = self.sales_channel.currency
        price = product_data.get('sales_price')
        rrp = product_data.get('regular_price')
        return {
            "price": price,
            "rrp": rrp,
            "currency": currency,
        }

    def get_structured_product_data(self, product_data):
        """
        Compile all of the different parts from the various "getters"
        """
        base_product_data, is_variation = self.get_base_product_data(product_data)
        # A few notes about attribute data:
        # - Woocommerce contains the simple product properties on the parent.
        #  that means we need to store them and apply the on the variations later on.
        # - There is no such things as a product-type like Tshirt or Table
        # - There are 2 types of attributes,
        #    some "global" which need mirror models
        #    others do not have mirror models - but may need them when getting pushed back.
        # - we have no way to tell the a "product type".
        # - but we can get what the product configurator data looks like base on the attributes
        #   and that variation data.
        attribute_data, configurable_attribute_data = self.get_attributes_for_product(product_data)
        images = self.get_attributes_for_product(product_data)
        prices = self.get_prices(product_data)

        raise NotImplemented('Attributes Read the NOTES!')

        return {
            "images": self.get_images(product_data),
            "attributes": self.get_attributes_for_product(product_data),
        }

    def get_images(self, remote_product: dict) -> list[dict]:
        """
        Convert images from the API to expected block which the ImportInstance will expect:
        [
            {
                "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg"
                "alt": '',
                "sort_order": 0,
                "is_main_image": True,
            }
        ]
        """
        source_images = remote_product.get("images", [])
        importer_images = []

        for index, image in enumerate(source_images):
            url = image.get("src")
            importer_images.append({
                "image_url": url,
                "alt": image.get("alt"),
                "sort_order": index,
                "is_main_image": index == 0,
            })
        return importer_images

    def get_attributes_for_product(self, remote_product: dict) -> tuple[list, list]:
        """
        Convert attributes from the API to the Importer Structure.

        There are 2 types of attributes:
        - Global Attributes: These are attributes that are not specific to a product.
        - Product Attributes: These are attributes that are specific to a product.

        We can also deduce configurator attributes based on the configurable product.

        will return both attribute data and configurable attribute data if relevant.
        But we have no way of creating a product-type for them. Which really sucks.

        Expected return for "attributes":
        [
            {
                "property": {
                "name": "Color",
                "type": "SELECT"
                },
                "value": "Blue"
            },
            {
                "property": {
                "name": "Size",
                "type": "SELECT"
                },
                "value": "L"
            }
            ],
            "prices": [
            {
                "price": 21.99,
                "currency": "GBP"
            }
        ]



        Make sure that you store all your remote_ids somehow because you need them later in your flow
        for all global attributes.
        """

        attributes = remote_product.get("attributes", [])
        for attribute in attributes:
            yield ImportAttributeInstance(attribute)

    def get_properties_data(self):
        """We will get the Global Attributes and return them """
        raise NotImplementedError("Not implemented")

    def get_select_values_data(self):
        """Get the terms from the Global Attributes"""
        raise NotImplementedError("Not implemented")

    def get_rules_data(self):
        """Woocommerce does not support rules. Nothing to do here."""
        return []

    def repair_remote_sku_if_needed(self, import_instance: ImportProductInstance):
        """
        Both products and variations can exist without skus.  We dont want that
        So instead we will populate our own skus.
        """
        remote_product = import_instance.remote_instance
        local_sku = import_instance.instance.sku

        if remote_product.is_variation:
            try:
                parent = remote_product.remote_parent_product
                parent_id = parent.remote_id
                variation_id = remote_product.remote_id
                self.api.update_product_variation(parent_id, variation_id, sku=local_sku)
            except AttributeError:
                msg = f"remote_product variation does not seem to have a parent product."
                raise SanityCheckError(msg)
        else:
            try:
                product_id = remote_product.remote_id
                self.api.update_poduct(product_id, sku=local_sku)
            except AttributeError:
                msg = f"remote_product does not seem to have a remote_id."
                raise SanityCheckError(msg)

        remote_product.remote_sku = local_sku
        remote_product.save()
        logger.info(f"Repaired remote_sku for product {remote_product.remote_id} using default_variant_id")

    def import_products_process(self):
        for product in self.api.get_products():
            # self.get_product_data(product)
            structured_data = self.get_structured_product_data(product)
            self.update_percentage()

            # Notes Below:

            # for remote_product in self.get_products():
            #     # The get_product_data creates the complate "importable dict"
            #     # The variations will get fetched in here.....BUT I need the remote_ids
            #     structured_data = self.get_structured_product_data(remote_product)
            #     importer_instance = ImportInstance(structured_data=structured_data, self.import_process)
            #     # Once converted the ddata and saved it localle, we want to create
            #     # the mirror models to ensure the when data is pushed to the server again
            #     # with changes, it doesnt end up with duplicates.

            #     # The trick is here:
            #     # A complate product is a compilation of all individial pieces:
            #     # ean
            #     # images
            #     # direct fields
            #     # This needs to be deconstructed again to handle them correctly remotely.

            #     # first create your import instance and assign remote_product.
            #     importer_instance.prepare_mirror_model_class(
            #         mirror_model_class=WoocommerceProduct,
            #         sales_channel=self.sales_channel,
            #         mirror_model_map={
            #             "local_instance": "*",  # * = self
            #         },
            #         mirror_model_defaults={
            #             "remote_sku": remote_product.get('sku'),
            #             "remote_id": remote_product.get('id'),
            #         }
            #     )

            #     importer_instance.process()
            #     # handle_remote_product will populate remote_instance inside of import_instance
            #     self.handle_ean_codes(importer_instance)
            #     self.handle_prices(importer_instance)
            #     self.handle_attributes(importer_instance)
            #     self.handle_translations(importer_instance)
            #     self.handle_images(importer_instance)
            #     # There I will have no remote_ids for the variations.
            #     self.handle_variations(importer_instance)

            #     #and if not a variations
            #     self.handle_assign(importer_instance)

            #     # self.set_field_if_exists('__image_index_to_remote_id')
            #     # self.set_field_if_exists('__mirror_product_properties_map')
            #     # self.set_field_if_exists('__variation_sku_to_id_map')
