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
        item = SimpleNamespace(sku="SKU1", nested=SimpleNamespace(value=5))

        data = serialize_listing_item(item)
        self.assertEqual(data["sku"], "SKU1")
        self.assertEqual(data["nested"]["value"], 5)


class AsyncImportAndItemFactoryTest(TestCase):
    def test_async_import_runs_and_item_factory_deserializes(self):
        imp = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company, remote_id="SELLER"
        )

        captured = []

        def fake_task(import_id, channel_id, product_data, is_last, updated_with):
            captured.append(product_data)

        class DummyImport(AsyncProductImportMixin):
            async_task = staticmethod(fake_task)

            def __init__(self, imp_process, sc, items):
                self.import_process = imp_process
                self.sales_channel = sc
                self._items = items

            def prepare_import_process(self):
                pass

            def strat_process(self):
                pass

            def process_completed(self):
                pass

            def get_total_instances(self):
                return len(self._items)

            def get_products_data(self):
                return self._items

        items = [SimpleNamespace(sku="X")]
        importer = DummyImport(imp, channel, items)
        importer.run()

        self.assertEqual(len(captured), 1)
        self.assertIsInstance(captured[0], dict)
        self.assertEqual(captured[0]["sku"], "X")

        processed = []

        class DummyClient:
            def __deserialize(self, data, klass):
                return SimpleNamespace(**data)

        with patch.object(
            AmazonProductItemFactory,
            "process_product_item",
            lambda self, prod: processed.append(prod),
        ), patch.object(
            AmazonProductItemFactory,
            "_get_client",
            return_value=DummyClient(),
        ):
            fac = AmazonProductItemFactory(captured[0], imp, channel)
            fac.run()

        self.assertEqual(len(processed), 1)
        self.assertIsInstance(processed[0], SimpleNamespace)
        self.assertEqual(processed[0].sku, "X")
