from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds.product_payloads import _MiraklFeedPersistenceMixin
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductIssue,
    MiraklProductType,
    MiraklSalesChannel,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class _TestMiraklFeedPersistenceFactory(_MiraklFeedPersistenceMixin):
    feed_action = MiraklSalesChannelFeedItem.ACTION_UPDATE

    def __init__(self, *, sales_channel, remote_instance, view) -> None:
        self.sales_channel = sales_channel
        self.remote_instance = remote_instance
        self.view = view


class MiraklFeedIssueResetTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
        )
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
        )

    def test_persisting_feed_rows_clears_existing_mirakl_product_issues(self):
        self.remote_product.set_new_sync_percentage(100)
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="1000",
            code="1000",
            severity="ERROR",
            raw_data={"source": "transformation_error_report_error"},
        )
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="MCM-05000",
            code="MCM-05000",
            severity="WARNING",
            raw_data={"source": "warning"},
        )

        factory = _TestMiraklFeedPersistenceFactory(
            sales_channel=self.sales_channel,
            remote_instance=self.remote_product,
            view=self.view,
        )

        item = factory._persist_feed_rows(
            product_type=self.product_type,
            rows=[{"sku": "SKU-1"}],
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.status, MiraklSalesChannelFeedItem.STATUS_PENDING)
        self.assertFalse(MiraklProductIssue.objects.filter(remote_product=self.remote_product).exists())
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_PENDING_APPROVAL)
