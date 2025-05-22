
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

    def get_product_data(self, product: dict, is_variation: bool = False, variation_name: str = None, parent_product_type: str = None):
        # variants = product.get("variants", {}).get("edges", [])
        # is_configurable = len(variants) > 1
        # product_type = Product.CONFIGURABLE if is_configurable else Product.SIMPLE

        # rule_product_type = product.get("productType") if parent_product_type is None else parent_product_type
        # active = product.get("status") == "ACTIVE"
        # structured_data = {
        #     "name": product.get("title"),
        #     "type": product_type,
        #     "active": active,
        #     "product_type": rule_product_type,
        # }

        # if product_type == Product.SIMPLE and variants:
        #     first_variant = variants[0]["node"]

        #     sku = first_variant.get("sku")

        #     if sku:
        #         structured_data["sku"] = sku

        #     inventory_policy = first_variant.get("inventoryPolicy")
        #     structured_data["allow_backorder"] = inventory_policy == "CONTINUE"
        #     structured_data["ean_code"] = first_variant.get("barcode")

        # structured_data['translations'] = self.get_product_translations(product, variation_name)
        # structured_data['images'], structured_data['__image_index_to_remote_id'] = self.get_product_images(product)

        # if product_type == Product.SIMPLE:
        #     structured_data['attributes'], structured_data['configurator_select_values'], structured_data['__mirror_product_properties_map'] = self.get_product_attributes(product)
        #     structured_data['prices'] = self.get_product_prices(product)

        # if product_type == Product.CONFIGURABLE:
        #     structured_data['variations'], structured_data['__variation_sku_to_id_map'] = self.get_product_variations(product, parent_active=active)

        # import_instance = ImportProductInstance(
        #     data=structured_data,
        #     import_process=self.import_process
        # )

        # import_instance.prepare_mirror_model_class(
        #     mirror_model_class=ShopifyProduct,
        #     sales_channel=self.sales_channel,
        #     mirror_model_map={"local_instance": "*"},
        #     mirror_model_defaults={"remote_id": product["id"], 'is_variation': is_variation}
        # )

        # import_instance.process()

        # self.update_remote_product(import_instance, product, is_variation)
        # self.create_log_instance(import_instance, structured_data)
        # self.handle_ean_code(import_instance)
        # self.handle_attributes(import_instance)
        # self.handle_translations(import_instance)
        # self.handle_prices(import_instance)
        # self.handle_images(import_instance)
        # self.handle_variations(import_instance)
        # self.handle_sales_channels_views(import_instance, product)

        return import_instance.instance

    def import_products_process(self):
        for product in self.api.get_products():
            self.get_product_data(product)
            self.update_percentage()
