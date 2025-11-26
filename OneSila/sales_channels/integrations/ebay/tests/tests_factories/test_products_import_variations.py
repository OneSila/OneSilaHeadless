"""Tests for the eBay product import variation handling."""

from __future__ import annotations

from unittest.mock import Mock, PropertyMock, patch

from core.tests import TestCase
from imports_exports.models import Import
from model_bakery import baker
from products.product_types import CONFIGURABLE, SIMPLE
from sales_channels.integrations.ebay.factories.imports.products_imports import (
    EbayProductsImportProcessor,
)
from sales_channels.integrations.ebay.models import EbayProduct, EbaySalesChannel
from sales_channels.models.products import RemoteProductConfigurator


class DummyImportInstance:
    def __init__(self, *, remote_instance, instance, data=None, rule=None) -> None:
        self.remote_instance = remote_instance
        self.instance = instance
        self.data = data or {}
        self.rule = rule


class EbayProductsImportProcessorVariationsTest(TestCase):
    """Validate variation linking for the eBay import processor."""

    def setUp(self) -> None:
        super().setUp()
        self.import_process = baker.make(Import, multi_tenant_company=self.multi_tenant_company)
        self.get_api_patcher = patch(
            "sales_channels.integrations.ebay.factories.mixins.GetEbayAPIMixin.get_api",
            return_value=None,
        )
        self.get_api_patcher.start()
        self.addCleanup(self.get_api_patcher.stop)
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="test.ebay.local",
        )
        self.processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

    def _create_products(self, *, child_sku: str) -> tuple[EbayProduct, EbayProduct]:
        parent_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=CONFIGURABLE,
            sku="PARENT",
        )
        child_product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=SIMPLE,
            sku=child_sku,
        )
        baker.make(
            "products.ConfigurableVariation",
            multi_tenant_company=self.multi_tenant_company,
            parent=parent_product,
            variation=child_product,
        )

        remote_parent = baker.make(
            EbayProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent_product,
            remote_sku="PARENT",
            is_variation=False,
        )
        remote_variation = baker.make(
            EbayProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_sku=None,
            is_variation=False,
        )

        return remote_parent, remote_variation

    def test_links_remote_variation_and_waits_for_remaining_children(self) -> None:
        remote_parent, remote_variation = self._create_products(child_sku="CHILD1")
        dummy_import = DummyImportInstance(
            remote_instance=remote_variation,
            instance=remote_variation.local_instance,
            data={"sku": "CHILD1"},
        )
        self.processor._parent_child_sku_map = {"PARENT": {"CHILD1", "CHILD2"}}

        with patch(
            "sales_channels.integrations.ebay.factories.imports.products_imports.RemoteProductConfigurator.objects.create_from_remote_product"
        ) as mock_create:
            self.processor.handle_variations(import_instance=dummy_import, parent_skus={"PARENT"})

        remote_variation.refresh_from_db()
        self.assertTrue(remote_variation.is_variation)
        self.assertEqual(remote_variation.remote_parent_product_id, remote_parent.id)
        self.assertEqual(remote_variation.remote_sku, "CHILD1")
        self.assertEqual(self.processor._parent_child_sku_map["PARENT"], {"CHILD2"})
        mock_create.assert_not_called()

    @patch("sales_channels.models.products.RemoteProductConfigurator.update_if_needed")
    def test_updates_existing_configurator_on_last_child(self, mock_update: Mock) -> None:
        remote_parent, remote_variation = self._create_products(child_sku="CHILD1")
        RemoteProductConfigurator.objects.create(
            remote_product=remote_parent,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )

        rule = object()
        dummy_import = DummyImportInstance(
            remote_instance=remote_variation,
            instance=remote_variation.local_instance,
            data={"sku": "CHILD1"},
            rule=rule,
        )
        self.processor._parent_child_sku_map = {"PARENT": {"CHILD1"}}

        self.processor.handle_variations(import_instance=dummy_import, parent_skus={"PARENT"})

        remote_variation.refresh_from_db()
        self.assertTrue(remote_variation.is_variation)
        self.assertEqual(remote_variation.remote_parent_product_id, remote_parent.id)
        self.assertNotIn("PARENT", self.processor._parent_child_sku_map)

        mock_update.assert_called_once()
        self.assertEqual(mock_update.call_args.kwargs["send_sync_signal"], False)
        self.assertIs(mock_update.call_args.kwargs["rule"], rule)
        self.assertTrue(
            mock_update.call_args.kwargs["variations"].filter(sku="CHILD1").exists()
        )

    def test_creates_configurator_when_missing_on_last_child(self) -> None:
        remote_parent, remote_variation = self._create_products(child_sku="CHILD1")
        rule = object()
        dummy_import = DummyImportInstance(
            remote_instance=remote_variation,
            instance=remote_variation.local_instance,
            data={"sku": "CHILD1"},
            rule=rule,
        )
        self.processor._parent_child_sku_map = {"PARENT": {"CHILD1"}}

        with patch(
            "sales_channels.integrations.ebay.factories.imports.products_imports.RemoteProductConfigurator.objects.create_from_remote_product"
        ) as mock_create:
            self.processor.handle_variations(import_instance=dummy_import, parent_skus={"PARENT"})

        remote_variation.refresh_from_db()
        self.assertTrue(remote_variation.is_variation)
        self.assertEqual(remote_variation.remote_parent_product_id, remote_parent.id)
        self.assertNotIn("PARENT", self.processor._parent_child_sku_map)
        mock_create.assert_called_once()
        self.assertEqual(mock_create.call_args.kwargs["remote_product"], remote_parent)
        self.assertIs(mock_create.call_args.kwargs["rule"], rule)
        self.assertTrue(
            mock_create.call_args.kwargs["variations"].filter(sku="CHILD1").exists()
        )
