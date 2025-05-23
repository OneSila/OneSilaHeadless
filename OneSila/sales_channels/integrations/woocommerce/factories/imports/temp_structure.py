from dataclasses import dataclass, field
from properties.models import Property
from typing import Set, List
from core.decorators import timeit_and_log
from django.utils import timezone

from .exceptions import UnknownTempPropertyClass

import logging
logger = logging.getLogger(__name__)


@dataclass
class TempPropertyClass:
    slug: str = None
    id: int = None
    name: str = None
    options: Set[str] = field(default_factory=set)
    variation: bool = False
    remote_id: int = None

    @property
    def property_type(self) -> str:
        if len(self.options) > 1:
            return Property.TYPES.MULTISELECT
        else:
            return Property.TYPES.SELECT

    @property
    def used_for_configurator(self) -> bool:
        return self.variation

    def identifier_for_payload(self) -> str:
        if self.slug:
            return 'internal_name', self.slug
        else:
            return 'name', self.name

    def property_attributes(self) -> dict:
        attributes = {
            "is_public_information": True,
            "add_to_filters": False,
        }
        if self.variation:
            attributes["add_to_filters"] = True

        return attributes


class TempPropertyDataConstructer:
    """
    Woocommerce has no real central attribute managment.  It's partially managed in global
    attributes. But even there, it doesnt have a single-select vs multi-select distinction.

    The same goes on the "local" / "product" attributes. Everything is multi-select.

    For things to work in OneSila, expescially the configurator, we need to know which attributes
    are of which property_type.

    This class will fetch all of the attributes across the woocommerce and try to determine
    the expected property_type for each attribute.

    That result can then be used in the ImportProcessor to determine the expected property_type for each attribute.
    And to determine which are local and global attributes for tracking.

    # Challenges:
    - global attributes have slugs and ids to identify them with.
    - product attributes only have a name.
    - variations are determined both on the config and variation.

    # Data structure:
    {
        "name": TempPropertyClass(
            slug="colour",
            id=1,
            name="Colour",
            options=["Red", "Blue", "Green"],
            variation=False
        )
    }
    We will loop through all of the known values and adjust the TempPropertyClass as needed.
    In the end we ought to have the information we need to make good decisions further down the line.

    # Usage:
    After running the run() method you will find the
    `processed_attributes` field populated with the TempPropertyClass instances.
    """

    def __init__(self, api):
        self.api = api
        self.processed_attributes = {}

    @timeit_and_log(logger, "fetching products from the API")
    def set_products(self) -> List[dict]:
        """
        Fetch all products from the API.
        """
        self.products = self.api.get_products()
        logger.info(f"Product count: {len(self.products)}")

    @timeit_and_log(logger, "fetching product attributes from the API")
    def set_product_attributes(self):
        """
        Fetch all attributes for all products from the API.
        """
        self.product_attributes = [
            attr
            for product in self.products
            for attr in product.get('attributes', [])
        ]

    @timeit_and_log(logger, "fetching variation attributes from the API")
    def set_variations(self) -> List[dict]:
        """
        Fetch all variations_data for each product from get_products()
        and fetch the variation data for each product.
        """
        self.variations = [
            variation
            for product in self.products
            for variation in self.api.get_product_variations(product.get('id'))
        ]
        logger.info(f"Variation count: {len(self.variations)}")

    @timeit_and_log(logger, "fetching variation attributes from the API")
    def set_variation_attributes(self) -> List[dict]:
        """
        Fetch all attributes for every variation from all products.
        """
        self.variation_attributes = [
            attr
            for variation in self.variations
            for attr in variation.get('attributes', [])
        ]

    def process_single_attribute(self, attribute: dict):
        """
        return the fields needed to populate the TempPropertyClass
        """
        name = attribute.get('name', None)
        slug = attribute.get('slug', None)
        id = attribute.get('id', None)
        options = set(attribute.get('options', []))
        variation = attribute.get('variation', False)

        return name, slug, id, options, variation

    def process_single_variation_attribute(self, attribute: dict):
        """
        return the fields needed to populate the TempPropertyClass
        adjusted for the varation attribute.
        """
        name = attribute.get('name', None)
        slug = attribute.get('slug', None)
        id = attribute.get('id', None)
        option = attribute.get('option', None)
        options = set([option]) if option else set()
        variation = attribute.get('variation', False)

        return name, slug, id, options, variation

    @timeit_and_log(logger, "processing attributes")
    def process_attributes(self, attributes: List[dict], variation_attribute: bool = False) -> None:
        """
        Process the attributes for all products and variations.
        """
        for prop in attributes:
            if variation_attribute:
                name, slug, id, options, variation = self.process_single_variation_attribute(prop)
            else:
                name, slug, id, options, variation = self.process_single_attribute(prop)

            try:
                temp_prop = self.processed_attributes[name]
                if temp_prop.id is None:
                    temp_prop.id = id

                if temp_prop.slug is None:
                    temp_prop.slug = slug

                if temp_prop.variation is False:
                    temp_prop.variation = variation

                temp_prop.options.update(options)
            except KeyError:
                self.processed_attributes[name] = TempPropertyClass(name=name, slug=slug, id=id, options=options, variation=variation)

    @timeit_and_log(logger, "run() prepping attribute data for structure analysis.")
    def run(self) -> dict[str, TempPropertyClass]:
        self.set_products()
        self.set_product_attributes()
        self.set_variations()
        self.set_variation_attributes()
        self.process_attributes(self.product_attributes, variation_attribute=False)
        self.process_attributes(self.variation_attributes, variation_attribute=True)

        logger.info(f"Total processed products: {len(self.products)}")
        logger.info(f"Total processed properties: {len(self.processed_attributes)}")
        logger.info(f"Properties: {self.processed_attributes}")

        return self.processed_attributes


class ImportProcessorTempStructureMixin:
    """
    This mixin will be used to add the temp structure to the import processor.
    """

    def prepare_import_process(self):
        super().prepare_import_process()
        self.temp_property_data_constructer = TempPropertyDataConstructer(self.api)
        self.temp_property_data_constructer.run()
        self.temp_property_data = self.temp_property_data_constructer.processed_attributes

    def find_temp_property_for_name(self, name) -> TempPropertyClass:
        """
        Find the temp property class for a given name.
        """
        try:
            return self.temp_property_data[name]
        except KeyError:
            raise UnknownTempPropertyClass(name=name)

    def create_payload_for_temp_property(self, temp_property: TempPropertyClass, options: List[str] | str) -> dict:
        """
        Create a payload for a temp property that matches the ImporterInstance payload requiremenets.
        {
            "property_data": {
                "name": "Color",
                "type": "SELECT"
            },
            "value": "Red",
        }
        """
        ptype = temp_property.property_type
        identifier, value = temp_property.identifier_for_payload()

        return {
            "property_data": {
                **temp_property.property_attributes(),
                identifier: value,
                "type": ptype
            },
            "value": options
        }

    def create_payload_for_property(self, name: str, options: List[str] | str) -> dict:
        """
        Create the desired payload for a property.
        """
        temp_property = self.find_temp_property_for_name(name)
        payload = self.create_payload_for_temp_property(temp_property, options)
        return payload
