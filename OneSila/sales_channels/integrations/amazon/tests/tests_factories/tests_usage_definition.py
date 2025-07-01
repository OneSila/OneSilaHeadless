from core.tests import TestCase
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import UsageDefinitionFactory
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.integrations.amazon.tests.schema_data import (
    BATTERY_SCHEMA,
    NUM_BATTERIES_SCHEMA,
    NUMBER_OF_LITHIUM_METAL_CELLS_SCHEMA,
    CUSTOMER_PACKAGE_TYPE_SCHEMA,
    POWER_PLUG_TYPE_SCHEMA,
    CONTROLLER_TYPE_SCHEMA,
    PRODUCT_SITE_LAUNCH_DATE_SCHEMA,
    COLOR_SCHEMA,
)
import json


class UsageDefinitionFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.public_definition = AmazonPublicDefinition.objects.create(
            product_type_code="BATTERY",
            raw_schema=BATTERY_SCHEMA["battery"],
            api_region_code="EU_UK",
            code="battery",
            name="Battery",
        )

    def test_battery_usage_definition(self):
        factory = UsageDefinitionFactory(self.public_definition)
        result = factory.run()
        data = json.loads(result)
        expected = {
            "battery": [
                {
                    "cell_composition": [
                        {"value": "%value:battery__cell_composition%"}
                    ],
                    "cell_composition_other_than_listed": [
                        {
                            "value": "%value:battery__cell_composition%",
                            "language_tag": "%auto:language%"
                        }
                    ],
                    "iec_code": [
                        {"value": "%value:battery__iec_code%"}
                    ],
                    "weight": [
                        {
                            "value": "%value:battery__weight%",
                            "unit": "%unit:weight%"
                        }
                    ],
                    "marketplace_id": "%auto:marketplace_id%"
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_num_batteries_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="POWER",
            raw_schema=NUM_BATTERIES_SCHEMA["num_batteries"],
            api_region_code="EU_UK",
            code="num_batteries",
            name="Number of Batteries",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "num_batteries": [
                {
                    "marketplace_id": "%auto:marketplace_id%",
                    "quantity": "%value:num_batteries__quantity%",
                    "type": "%value:num_batteries__type%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_number_of_lithium_metal_cells_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="POWER_LITHIUM",
            raw_schema=NUMBER_OF_LITHIUM_METAL_CELLS_SCHEMA["number_of_lithium_metal_cells"],
            api_region_code="EU_UK",
            code="number_of_lithium_metal_cells",
            name="Number of Lithium Metal Cells",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "number_of_lithium_metal_cells": [
                {
                    "value": "%value:number_of_lithium_metal_cells%",
                    "marketplace_id": "%auto:marketplace_id%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_customer_package_type_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="PACKAGING",
            raw_schema=CUSTOMER_PACKAGE_TYPE_SCHEMA["customer_package_type"],
            api_region_code="EU_UK",
            code="customer_package_type",
            name="Customer Package Type",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "customer_package_type": [
                {
                    "value": "%value:customer_package_type%",
                    "language_tag": "%auto:language%",
                    "marketplace_id": "%auto:marketplace_id%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_power_plug_type_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="PLUG",
            raw_schema=POWER_PLUG_TYPE_SCHEMA["power_plug_type"],
            api_region_code="EU_UK",
            code="power_plug_type",
            name="Power Plug Type",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "power_plug_type": [
                {
                    "value": "%value:power_plug_type%",
                    "marketplace_id": "%auto:marketplace_id%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_controller_type_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="CONTROLLER",
            raw_schema=CONTROLLER_TYPE_SCHEMA["controller_type"],
            api_region_code="EU_UK",
            code="controller_type",
            name="Controller Type",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "controller_type": [
                {
                    "value": "%value:controller_type%",
                    "language_tag": "%auto:language%",
                    "marketplace_id": "%auto:marketplace_id%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_product_site_launch_date_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="LAUNCH_DATE",
            raw_schema=PRODUCT_SITE_LAUNCH_DATE_SCHEMA["product_site_launch_date"],
            api_region_code="EU_UK",
            code="product_site_launch_date",
            name="Product Site Launch Date",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "product_site_launch_date": [
                {
                    "marketplace_id": "%auto:marketplace_id%",
                    "value": "%value:product_site_launch_date%",
                }
            ]
        }
        self.assertEqual(data, expected)

    def test_color_usage_definition(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="COLOR",
            raw_schema=COLOR_SCHEMA["color"],
            api_region_code="EU_UK",
            code="color",
            name="Color",
        )

        factory = UsageDefinitionFactory(definition)
        result = factory.run()
        data = json.loads(result)

        expected = {
            "color": [
                {
                    "standardized_values": ["%value:color%"],
                    "value": "%value:color%",
                    "language_tag": "%auto:language%",
                    "marketplace_id": "%auto:marketplace_id%",
                }
            ]
        }
        self.assertEqual(data, expected)

