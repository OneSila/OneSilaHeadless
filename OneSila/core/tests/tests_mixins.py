from model_bakery import baker

from core.tests import TestCase
from core.mixins import TemporaryDisableInspectorSignalsMixin
from products.models import SimpleProduct
from products_inspector.constants import MISSING_PRICES_ERROR


class DummyProcess(TemporaryDisableInspectorSignalsMixin):
    def __init__(self, company):
        self.multi_tenant_company = company


class TemporaryDisableInspectorSignalsMixinTestCase(TestCase):
    def test_disable_and_refresh_inspector_signals(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=False,
        )
        block = product.inspector.blocks.get(error_code=MISSING_PRICES_ERROR)
        self.assertTrue(block.successfully_checked)

        other_company = baker.make("core.MultiTenantCompany")
        other_product = SimpleProduct.objects.create(
            multi_tenant_company=other_company,
            active=False,
        )
        other_block = other_product.inspector.blocks.get(error_code=MISSING_PRICES_ERROR)
        self.assertTrue(other_block.successfully_checked)

        proc = DummyProcess(self.multi_tenant_company)
        proc.disable_inspector_signals()

        product.active = True
        product.save()

        other_product.active = True
        other_product.save()

        block.refresh_from_db()
        other_block.refresh_from_db()
        self.assertTrue(block.successfully_checked)
        self.assertFalse(other_block.successfully_checked)
        self.assertIn(product.sku, proc.skipped_inspector_sku)
        self.assertNotIn(other_product.sku, proc.skipped_inspector_sku)

        proc.refresh_inspector_status()
        block.refresh_from_db()
        self.assertFalse(block.successfully_checked)
