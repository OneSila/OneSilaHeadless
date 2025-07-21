from sales_channels.integrations.woocommerce.factories.imports.product_imports import WoocommerceProductImportProcessor
from imports_exports.models import Import
from .mixins import TestCaseWoocommerceMixin
from currencies.models import PublicCurrency
from currencies.currencies import currencies

import logging
logger = logging.getLogger(__name__)


class TestWoocommerceProductImportProcessor(TestCaseWoocommerceMixin):
    remove_woocommerce_mirror_and_remote_on_teardown = False

    def test_woocommerce_import_product(self):
        # FIXME: Strangely enough the migratoins seems to skip public currencies
        # or something is emptying them. Very odd. We create it manually for now.
        PublicCurrency.objects.get_or_create(**currencies['GB'])
        import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        processor = WoocommerceProductImportProcessor(
            import_process=import_process,
            sales_channel=self.sales_channel,
        )
        processor.run()
