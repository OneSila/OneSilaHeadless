from unittest.mock import patch

from core.tests import TestCase
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models.properties import AmazonProductType


class AmazonProductTypeReceiversTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )

    @patch("sales_channels.integrations.amazon.receivers.create_amazon_product_type_rule_task")
    def test_factory_run_triggered_on_imported_change(self, task_func):
        pt = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="CHAIR",
            imported=False,
        )

        pt.imported = True
        pt.save()

        task_func.assert_called_once_with(
            product_type_code=pt.product_type_code,
            sales_channel_id=pt.sales_channel_id,
        )
