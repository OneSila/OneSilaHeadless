from sales_channels.factories.imports import SalesChannelImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportProductPropertiesRuleInstance
from products.models import Product
from core.decorators import timeit_and_log

from ..exceptions import SanityCheckError
from ..mixins import GetWoocommerceAPIMixin
from .temp_structure import ImportProcessorTempStructureMixin
from sales_channels.integrations.woocommerce.constants import EAN_CODE_WOOCOMMERCE_FIELD_NAME, \
    DEFAULT_PRODUCT_TYPE

from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, \
    WoocommerceEanCode, WoocommercePrice, WoocommerceCurrency, \
    WoocommerceMediaThroughProduct, WoocommerceRemoteLanguage
from products.helpers import generate_sku
from typing import Tuple, List, Set
from django.db.utils import IntegrityError
from decimal import Decimal

import logging

from ...exceptions import UnsupportedProductTypeError

logger = logging.getLogger(__name__)


class WoocommerceProductImportProcessor(ImportProcessorTempStructureMixin, SalesChannelImportMixin, GetWoocommerceAPIMixin):
    remote_imageproductassociation_class = WoocommerceMediaThroughProduct
    remote_price_class = WoocommercePrice
    remote_ean_code_class = WoocommerceEanCode

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, sales_channel, language)

        logger.debug(
            f"Initializing WoocommerceProductImportProcessor for sales channel: {sales_channel}. "
            f"Import process: {import_process}, {type(import_process)} "
            f"id: {import_process.id=}. "
        )

        self.repair_sku_map = {}
        self.api = self.get_api()

        self.language = WoocommerceRemoteLanguage.objects.get(
            sales_channel=self.sales_channel,
        ).local_instance
        self.currency = WoocommerceCurrency.objects.get(
            sales_channel=self.sales_channel,
        ).local_instance
        self.currency_iso_code = self.currency.iso_code

    def get_total_instances(self) -> int:
        attribute_work = 1  # it's A lot more then 1. But what else to do??
        get_product_data_work = 1
        product_work = self.api.get_product_count()
        return sum([attribute_work, get_product_data_work, product_work])

    @timeit_and_log(logger, "fetching products from the API")
    def set_product_data(self) -> List[dict]:
        """
        Fetch products from the API and return all of them.
        """
        self.product_data = self.api.get_products()

    def get_tax_class(self, product_data: dict) -> dict:
        remote_tax_class = product_data.get('tax_status')
        return None

    def get_base_product_data(self, product_data: dict, parent_sku=None) -> Tuple[dict, bool]:
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
        ptype = product_data.get('type', 'unknown')
        is_configurable = False

        if ptype == 'simple':
            local_type = Product.SIMPLE
            is_variation = False
        elif ptype == 'variable':
            local_type = Product.CONFIGURABLE
            is_variation = False
            is_configurable = True
        elif ptype == 'variation':
            local_type = Product.SIMPLE
            is_variation = True
        else:
            raise UnsupportedProductTypeError(ptype)

        try:
            active = product_data["status"] == "publish" and product_data["catalog_visibility"] == "visible"
        except KeyError:
            # Most likely a variation we only use the status
            # catalog_visibility seems to be missing.
            active = product_data["status"] == "publish"

        payload = {
            'name': product_data.get('name'),
            'active': active,
            'type': local_type,
            # We're adding a default type to ensure users get to see their data.
            # and we don't have unexpected sync issues due to missing product_type.
            'product_type': DEFAULT_PRODUCT_TYPE,
        }

        # Woocommerce is not consistent with the sku field.
        # variations seems to get the parent sku.
        sku = product_data.get('sku')
        if sku != parent_sku:
            payload['sku'] = sku

        ean_code = product_data.get(EAN_CODE_WOOCOMMERCE_FIELD_NAME)
        if not is_configurable and ean_code:
            payload['ean_code'] = ean_code

        return payload, is_variation, is_configurable

    def get_content(self, product_data: dict) -> List[dict]:
        """
        return the product content / tranlsations
        """
        name = product_data.get('name')
        short_description = product_data.get('short_description')
        description = product_data.get('description')
        url_key = product_data.get('slug')

        return [{
            'language': self.language,
            'name': name,
            'short_description': short_description,
            'description': description,
            'url_key': url_key,
        }]

    def get_prices(self, product_data: dict, is_variation: bool = False, parent_data: dict = None) -> dict:
        """
        get the price data
        [{ "price": 19.99,
        "currency": "GBP" }]

        or None if this is a configurable product.
        """
        price = product_data.get('sale_price', None)
        rrp = product_data.get('regular_price', None)

        # it is likely that a variation does not have a direct price, but instead it
        # uses the parent price in woocommerce.  Let's account for that.
        if is_variation and not (price or rrp):
            price = parent_data.get('sale_price', None)
            rrp = parent_data.get('regular_price', None)

        payload = {}
        if price:
            payload['price'] = Decimal(price)

        if rrp:
            payload['rrp'] = Decimal(rrp)

        # if there are no prices, no point adding a currency
        # In case you're wondering...yes...woocommerce can have
        # products WITHOUT prices.
        if payload:
            payload['currency'] = self.currency_iso_code

        payload = [payload] if payload else []
        logger.info(f"Prices payload: {payload}")
        return payload

    def get_structured_product_data(self, product_data: dict) -> dict:
        """
        Compile all of the different parts from the various "getters"
        """
        base_product_data, is_variation, is_configurable = self.get_base_product_data(product_data)
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
        properties_data = self.get_properties_data_for_product(product_data)
        images = self.get_images(product_data)
        prices = self.get_prices(product_data)
        tax = self.get_tax_class(product_data)
        translation = self.get_content(product_data)

        # Now that we have all of the data, let's build th actual payload.
        payload = {
            **base_product_data,
            'images': images,
            'properties': properties_data,
        }

        if tax:
            payload['vat_rate'] = tax

        if not is_configurable:
            payload['prices'] = prices

        if translation:
            payload['translations'] = translation

        logger.debug(f"Structured product data: {payload}")

        return payload, is_variation

    def get_images(self, remote_product: dict) -> List[dict]:
        """
        Convert images from the API to expected block which the ImportInstance will expect:
        [
            {
                "image_url": "https://2./0266554465.jpeg"
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

    def get_properties_data_for_product(self, product_data: dict, is_variation=False, parent_data: dict = None) -> Tuple[List[dict], List[dict]]:
        """
        Convert attributes from the API to the Importer Structure.

        There are 2 types of attributes for configurable products and simple products
        - Global Attributes: These are attributes that are not specific to a product.
        - Product Attributes: These are attributes that are specific to a product.

        On variation products, we only have the configurator attributes present.

        This means that:
        - the configurator structure can be deduced from the product and parent (variation:True) together.
        - all other attributes come from the partent.
        - we still need to handle global vs product attributes for every attribute entry.

        In order to ensure we have a clean payload, we will not keep the variaton data
        from the parent in the get_product_data stuff.  Instead we will request the parent
        attribute data for each variation (yes..a few extra calls) and create a clean
        flow where we can also cleanly identify which attributes are used in the configurator.

        The main challenge is....how do we handle this globally?
        It seems like we must pull all products first. Compare all the product-data attribues in order
        to decide which Property Types they are.  And limit ourselves to Select vs MultiSelect.

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

        remote_product['attributes'] will look something like:
            [{
            "id": 1,
            "name": "Size",
            "position": 0,
            "visible": true,
            "variation": true,
            "options": [
                "Small",
                "Medium",
                "Large"]
            }]

        Make sure that you store all your remote_ids somehow because you need them later in your flow
        for all global attributes.
        """

        attributes = []

        # Configurable products hold no properties in OneSila.
        # Don't force them.  Just return an empty list and leave
        # the propety stuff for simples/bundles/aliases.
        if is_variation:
            parent_attributes = parent_data.get('attributes', [])
            variation_attributes = product_data.get('attributes', [])

            for attribute in parent_attributes:
                name = attribute.get('name')
                options = attribute.get('options')
                payload = self.create_payload_for_property(name, options)
                attributes.append(payload)

            for attribute in variation_attributes:
                name = attribute.get('name')
                option = attribute.get('option')
                payload = self.create_payload_for_property(name, option)
                attributes.append(payload)
        else:
            remote_attributes = product_data.get("attributes", [])
            for attribute in remote_attributes:
                name = attribute.get('name')
                options = attribute.get('options')
                payload = self.create_payload_for_property(name, options)
                attributes.append(payload)

        return attributes

    def get_properties_data(self):
        """We will get the Global Attributes and return them """
        return []

    def get_select_values_data(self):
        """Get the terms from the Global Attributes"""
        return []

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

    def assign_to_saleschannelview(self, importer_instance: ImportProductInstance):
        """
        Assign the product to the sales channel view.
        """

        sales_channel_view = self.sales_channel.saleschannelview_set.get(
            multi_tenant_company=self.import_process.multi_tenant_company
        )

        try:
            assign, created = SalesChannelViewAssign.objects.get_or_create(
                product=importer_instance.instance,
                sales_channel_view=sales_channel_view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                remote_product=importer_instance.remote_instance,
                sales_channel=self.sales_channel,
            )
        except IntegrityError as e:
            # Somehow it can happen that an assign will alrady exist - but perhaps
            # with anothe remote product.  In that case, just remove it and
            # re-run thi method.
            logger.warning(
                f"SalesChannelViewAssign seems to exist for another remote product. (Product: {importer_instance.instance}). Removing and re-creating.")
            assign = SalesChannelViewAssign.objects.get(
                product=importer_instance.instance,
                sales_channel_view=sales_channel_view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
            )
            assign.delete()
            return self.assign_to_saleschannelview(importer_instance)

        return assign, created

    def update_remote_product_sync_percentage(self, import_instance: ImportProductInstance, product: dict, is_variation: bool):
        remote_product = import_instance.remote_instance
        remote_product.syncing_current_percentage = 100
        remote_product.save()

    def process_parent_product(self, remote_product: dict):
        """
        Process a single product being a Configurable or Simple product.
        Variations are process elsewhere through process_variation().
        """
        # The get_product_data creates the complate "importable dict"
        # The variations will get fetched in here.....BUT I need the remote_ids
        # structured_data = self.get_structured_product_data(remote_product)
        # importer_instance = ImportInstance(structured_data=structured_data, self.import_process)
        # Once converted the ddata and saved it locally, we want to create
        # the mirror models to ensure the when data is pushed to the server again
        # with changes, it doesnt end up with duplicates.
        structured_data, is_variation = self.get_structured_product_data(remote_product)
        property_data = structured_data.get('properties', [])

        # The trick is here:
        # A complete product is a compilation of all individial pieces:
        # ean
        # images
        # direct fields
        # This needs to be deconstructed again to handle them correctly remotely.
        parent_sku = structured_data.get('sku')
        remote_id = remote_product.get('id')
        # Check manually in woocomemrce if the variation DOES have an sku
        # if not, we must set it in advance or later efforts become
        # to complicated to inject skus after import
        # if not parent_sku:
        #     parent_sku = generate_sku()
        #     structured_data['sku'] = parent_sku
        #     self.api.update_product(remote_id, sku=parent_sku)

        local_product = None
        remote_product_instance = WoocommerceProduct.objects.filter(remote_id=remote_id, sales_channel=self.sales_channel).first()
        if remote_product_instance:
            local_product = remote_product_instance.local_instance

        # first create your import instance and assign remote_product.
        parent_importer_instance = ImportProductInstance(
            data=structured_data,
            import_process=self.import_process,
            instance=local_product
        )
        parent_importer_instance.prepare_mirror_model_class(
            mirror_model_class=WoocommerceProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={
                "local_instance": "*",  # * = self
            },
            mirror_model_defaults={
                # Skus are not always present.
                # "remote_sku": structured_data.get('sku'),
                "remote_id": remote_product.get('id'),
                "is_variation": is_variation,
            },
        )
        parent_importer_instance.process()

        # For completeness, let's set the sku on the mirror model.
        # FIXME: Setting the sku on the remote-product seems to fail the import process
        # in a silent way.
        # remote_instance = parent_importer_instance.remote_instance
        # remote_instance.remote_sku = parent_sku
        # remote_instance.save()
        return parent_importer_instance

    def process_variation(self, variation_id: str, parent_importer_instance: ImportProductInstance, parent_data: dict):
        """
        Process a single variation in it's own importer instance to ensure
        we have full controle over the mirror models and get to set the remote ids cleanly.

        variation_id = woocommerce variation id from the parent payload
        parent_importer_instance = the importer instance for the parent product
        parent_data = the parent data from the parent payload. As in the raw woocommerce payload.
        """

        # We need to remove the variation data from the structured data
        # and call a variation import process for each variations
        # because we need to controle the mirror_model_class + remote_id + parent_id stuff....

        # Once done.... you must set the "remote_parent_product" on the freshly created mirror
        # variationimporter_instance.remote_instance.remote_parent_product = parent_importer_instance.remote_instance
        parent_remote_id = parent_importer_instance.remote_instance.remote_id
        parent_sku = parent_importer_instance.instance.sku
        variation_data = self.api.get_product_variation(parent_remote_id, variation_id)

        # variation_sku = variation_data.get('sku')
        # Check manually in woocomemrce if the variation DOES have an sku
        # if not, we must set it in advance or later efforts become
        # to complicated to inject skus after import
        # if variation_sku == parent_sku or not variation_sku:
        #     variation_sku = generate_sku()
        #     self.api.update_product_variation(parent_remote_id, variation_id, sku=variation_sku)
        #     variation_data['sku'] = variation_sku

        base_product_data, *_ = self.get_base_product_data(variation_data, parent_sku=parent_sku)
        properties_data = self.get_properties_data_for_product(variation_data, is_variation=True, parent_data=parent_data)
        images = self.get_images(variation_data)
        prices = self.get_prices(variation_data, is_variation=True, parent_data=parent_data)
        tax = self.get_tax_class(variation_data)

        payload = {
            **base_product_data,
            'properties': properties_data,
            'prices': prices,
            'vat_rate': tax,
            'images': images,
            'configurable_parent_sku': parent_sku,
        }

        local_product = None
        remote_product_instance = WoocommerceProduct.objects.filter(
            remote_id=variation_id, sales_channel=self.sales_channel, remote_parent_product__remote_id=parent_remote_id).first()
        if remote_product_instance:
            local_product = remote_product_instance.local_instance

        variation_importer_instance = ImportProductInstance(
            data=payload,
            import_process=self.import_process,
            instance=local_product
        )
        variation_importer_instance.prepare_mirror_model_class(
            mirror_model_class=WoocommerceProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={
                "local_instance": "*",  # * = self
            },
            mirror_model_defaults={
                "remote_id": variation_id,
                "remote_parent_product": parent_importer_instance.remote_instance,
                "is_variation": True,
            },
        )
        variation_importer_instance.process()

        # For completeness, let's set the sku on the mirror model.
        # FIXME: Setting the sku on the remote-product seems to fail the import process
        # in a silent way.
        # remote_product = variation_importer_instance.remote_instance
        # remote_product.remote_sku = variation_sku
        # remote_product.save()
        return variation_importer_instance

    def process_product_rule(self):
        product_rule_payload = self.create_product_rule_payload()
        product_rule_import_instance = ImportProductPropertiesRuleInstance(
            data=product_rule_payload,
            import_process=self.import_process,
        )
        product_rule_import_instance.process()

    @timeit_and_log(logger, "importing woocommerce product")
    def process_full_product(self, remote_product: dict):
        # First we to the top level product and assign it to the sales channel view.
        parent_data = remote_product
        parent_importer_instance = self.process_parent_product(parent_data)
        self.assign_to_saleschannelview(parent_importer_instance)
        self.update_remote_product_sync_percentage(parent_importer_instance,
            product=remote_product, is_variation=False)

        # One the top level product is done, we go ahead with the varitions.
        for variation_id in remote_product['variations']:
            variation_import_instance = self.process_variation(variation_id, parent_importer_instance, parent_data)
        # Dont forget about the counter.
        self.update_percentage()

    @timeit_and_log(logger, "importing all woocommerce products")
    def import_products_process(self):
        self.set_product_data()
        self.update_percentage()

        self.process_product_rule()
        self.update_percentage()

        for remote_product in self.product_data:
            try:
                self.process_full_product(remote_product)
            except UnsupportedProductTypeError as exc:
                logger.warning(str(exc))
                continue
