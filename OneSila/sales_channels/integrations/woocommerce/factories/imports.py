
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

    #
    # Fetch Data methods
    #

    def fetch_global_attributes(self):
        """
        Fetch global attributes from the API
        """
        return self.api.get_attributes()

    def fetch_global_attributes_terms(self, global_attribute_id):
        """
        Fetch global attributes terms from the API
        """
        return self.api.get_attribute_terms(global_attribute_id)

    def fetch_products(self):
        """
        Fetch products from the API
        """
        return self.api.get_products()

    def fetch_product_variations(self, product_id):
        """
        Fetch product variations from the API
        """
        return self.api.get_product_variations(product_id)

    #
    # Convert data to Importer Structure
    #

    def convert_images(self, remote_product: dict) -> Generator[ImportImageInstance]:
        """
        Convert images from the API to the Importer Structure
        """
        images = remote_product.get("images", [])
        for index, image in enumerate(images):
            url = image.get("src")
            yield ImportImageInstance({
                "image_url": url,
                "alt": image.get("alt"),
                "sort_order": index,
                "is_main_image": index == 0,
            })

    def convert_attributes(self, remote_product: dict):
        """
        Convert attributes from the API to the Importer Structure.

        There are 2 types of attributes:
        - Global Attributes: These are attributes that are not specific to a product.
        - Product Attributes: These are attributes that are specific to a product.
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
            self.get_product_data(product)
            self.update_percentage()
