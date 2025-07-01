from core.tests import TestCase
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import UsageDefinitionFactory
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.integrations.amazon.tests.schema_data import BATTERY_SCHEMA
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

