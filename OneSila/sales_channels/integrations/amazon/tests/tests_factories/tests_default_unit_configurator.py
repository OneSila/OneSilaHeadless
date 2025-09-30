from copy import deepcopy

from core.tests import TestCase
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import DefaultUnitConfiguratorFactory
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonDefaultUnitConfigurator,
)
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.integrations.amazon.tests.schema_data import BATTERY_SCHEMA


class DefaultUnitConfiguratorFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        from sales_channels.integrations.amazon.models import AmazonSalesChannelView
        self.view = AmazonSalesChannelView.objects.create(sales_channel=self.sales_channel, multi_tenant_company=self.multi_tenant_company)
        self.public_definition = AmazonPublicDefinition.objects.create(
            product_type_code="BATTERY",
            raw_schema=BATTERY_SCHEMA["battery"],
            api_region_code="EU_UK",
            code="battery",
            name="Battery",
        )

    def test_creates_configurator_for_weight_unit(self):
        factory = DefaultUnitConfiguratorFactory(
            self.public_definition, self.sales_channel, self.view, True
        )
        factory.run()

        configurator = AmazonDefaultUnitConfigurator.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.view,
            code="battery__weight",
        )

        expected_choices = [
            {"value": "grams", "name": "Grams"},
            {"value": "kilograms", "name": "Kilograms"},
            {"value": "milligrams", "name": "Milligrams"},
            {"value": "ounces", "name": "Ounces"},
            {"value": "pounds", "name": "Pounds"},
        ]

        self.assertEqual(configurator.name, "Battery Weight Unit")
        self.assertEqual(configurator.choices, expected_choices)

    def test_name_not_updated_when_not_default(self):
        # initial creation as default marketplace
        factory = DefaultUnitConfiguratorFactory(
            self.public_definition, self.sales_channel, self.view, True
        )
        factory.run()

        configurator = AmazonDefaultUnitConfigurator.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.view,
            code="battery__weight",
        )
        configurator.name = "Original Name"
        configurator.save()

        updated_schema = deepcopy(BATTERY_SCHEMA["battery"])
        updated_schema["items"]["properties"]["weight"]["items"]["properties"]["unit"][
            "title"
        ] = "Updated Title"
        self.public_definition.raw_schema = updated_schema
        self.public_definition.save()

        factory = DefaultUnitConfiguratorFactory(
            self.public_definition, self.sales_channel, self.view, False
        )
        factory.run()
        configurator.refresh_from_db()

        self.assertEqual(configurator.name, "Original Name")
