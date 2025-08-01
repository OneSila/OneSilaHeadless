from types import SimpleNamespace
from unittest.mock import patch

from core.tests import TestCase
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.models import Import
from sales_channels.integrations.amazon.factories.imports.products_imports import (
    AmazonProductItemFactory,
)
from sales_channels.integrations.amazon.helpers import serialize_listing_item
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
)


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
