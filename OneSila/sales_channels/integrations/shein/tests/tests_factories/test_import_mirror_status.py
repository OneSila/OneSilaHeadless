"""Tests for Shein import mirror status handling."""

from types import SimpleNamespace

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.factories.imports.product_mirrors import (
    SheinProductImportMirrorMixin,
)
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel


class _MirrorHarness(SheinProductImportMirrorMixin):
    def __init__(self, *, import_process, sales_channel) -> None:
        self.import_process = import_process
        self.sales_channel = sales_channel
        self.multi_tenant_company = sales_channel.multi_tenant_company

    def _extract_spu_name(self, *, payload):
        if not payload:
            return None
        return payload.get("spu_name")

    def _extract_skc_name(self, *, payload):
        if not payload:
            return None
        return payload.get("skc_name")

    def _extract_sku_code(self, *, payload):
        if not payload:
            return None
        return payload.get("sku_code")


class SheinImportMirrorStatusTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
        )

    def test_update_remote_product_sets_completed_status_on_import(self):
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="SKU-1",
            remote_id="SPU-1",
            spu_name="SPU-1",
            status=SheinProduct.STATUS_PENDING_APPROVAL,
            syncing_current_percentage=100,
        )
        import_instance = SimpleNamespace(
            data={"sku": "SKU-1"},
            remote_instance=remote_product,
        )

        mirror = _MirrorHarness(import_process=None, sales_channel=self.sales_channel)
        mirror.update_remote_product(
            import_instance=import_instance,
            spu_name="SPU-1",
            skc_name=None,
            sku_code=None,
            is_variation=False,
        )

        remote_product.refresh_from_db()
        self.assertEqual(remote_product.status, SheinProduct.STATUS_COMPLETED)
