from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from core.tests import TestCase
from django.utils import timezone
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.models import Import
from model_bakery import baker
from properties.models import Property
from sales_channels.integrations.amazon.factories.imports.products_imports import (
    AmazonProductItemFactory,
)
from sales_channels.integrations.amazon.helpers import serialize_listing_item
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonSalesChannelView
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
)
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from sales_channels.integrations.amazon.tasks import (
    refresh_amazon_product_issues_cronjob,
    run_amazon_sales_channel_mapping_sync,
)
from unittest.mock import PropertyMock, patch


class SerializationHelpersTest(TestCase):
    def test_serialize_listing_item(self):
        from types import SimpleNamespace

        item = SimpleNamespace(
            sku="SKU1",
            nested=SimpleNamespace(value=5),
            summaries=[
                SimpleNamespace(sku="SKU1", product_tpe="CHAIR"),
            ],
        )

        data = serialize_listing_item(item)

        # existing assertions
        self.assertEqual(data["sku"], "SKU1")
        self.assertEqual(data["nested"]["value"], 5)

        # new assertions for the summaries list
        self.assertIn("summaries", data)
        self.assertIsInstance(data["summaries"], list)
        self.assertEqual(len(data["summaries"]), 1)

        first = data["summaries"][0]
        self.assertIsInstance(first, dict)
        self.assertEqual(first["sku"], "SKU1")
        self.assertEqual(first["product_tpe"], "CHAIR")


class AmazonMappingSyncTaskTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)
        self.source_sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="source.example.com",
        )
        self.target_sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="target.example.com",
        )
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

    def test_run_amazon_sales_channel_mapping_sync(self):
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="color",
            local_instance=self.local_property,
        )
        target_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="color",
        )

        summary = run_amazon_sales_channel_mapping_sync(
            source_sales_channel_id=self.source_sales_channel.id,
            target_sales_channel_id=self.target_sales_channel.id,
        )

        target_property.refresh_from_db()

        self.assertEqual(summary["properties"], 1)
        self.assertEqual(summary["product_types"], 0)
        self.assertEqual(summary["select_values"], 0)
        self.assertEqual(summary["default_units"], 0)
        self.assertEqual(target_property.local_instance, self.local_property)