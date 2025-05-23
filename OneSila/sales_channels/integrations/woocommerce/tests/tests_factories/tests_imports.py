from sales_channels.integrations.woocommerce.factories.imports.product_imports import WoocommerceProductImportProcessor
from imports_exports.models import Import
from .mixins import TestCaseWoocommerceMixin

import logging
logger = logging.getLogger(__name__)


class TestWoocommerceProductImportProcessor(TestCaseWoocommerceMixin):
    def test_woocommerce_import_product(self):
        import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        processor = WoocommerceProductImportProcessor(
            import_process=import_process,
            sales_channel=self.sales_channel,
        )
        processor.run()
