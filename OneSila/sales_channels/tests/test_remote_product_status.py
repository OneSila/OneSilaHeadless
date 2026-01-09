from core.tests import TestCase
from integrations.models import IntegrationLog
from model_bakery import baker

from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import RemoteProduct, SalesChannelView, SalesChannelViewAssign


class RemoteProductStatusTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            "products.Product",
            type='SIMPLE',
            multi_tenant_company=self.multi_tenant_company,
        )

        self.remote_product = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.product,
            remote_sku="SKU-STATUS",
        )

    def test_status_transitions_follow_progress_and_errors(self):
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_PROCESSING)

        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_COMPLETED)

        IntegrationLog.objects.create(
            integration=self.sales_channel,
            remote_product=self.remote_product,
            action=IntegrationLog.ACTION_UPDATE,
            status=IntegrationLog.STATUS_FAILED,
        )

        self.remote_product.set_new_sync_percentage(0)
        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_FAILED)

        IntegrationLog.objects.filter(remote_product=self.remote_product).delete()
        self.remote_product.set_new_sync_percentage(0)
        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_COMPLETED)


class SalesChannelViewAssignStatusFilterTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view = baker.make(
            SalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Completed remote product
        self.product_completed = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product_completed = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.product_completed,
            remote_sku="SKU-COMPLETED",
        )
        self.remote_product_completed.set_new_sync_percentage(100)
        self.remote_product_completed.refresh_from_db()

        # Processing remote product (progress < 100)
        self.product_processing = baker.make(
            "products.Product",
            type='SIMPLE',
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product_processing = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.product_processing,
            remote_sku="SKU-PROCESSING",
        )
        self.remote_product_processing.set_new_sync_percentage(50)
        self.remote_product_processing.refresh_from_db()

        # Failed remote product (has errors)
        self.product_failed = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product_failed = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.product_failed,
            remote_sku="SKU-FAILED",
        )
        IntegrationLog.objects.create(
            integration=self.sales_channel,
            remote_product=self.remote_product_failed,
            action=IntegrationLog.ACTION_UPDATE,
            status=IntegrationLog.STATUS_FAILED,
        )
        self.remote_product_failed.set_new_sync_percentage(100)
        self.remote_product_failed.refresh_from_db()

        # Assigns
        self.assign_completed = SalesChannelViewAssign.objects.create(
            product=self.product_completed,
            sales_channel_view=self.view,
            remote_product=self.remote_product_completed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.assign_processing = SalesChannelViewAssign.objects.create(
            product=self.product_processing,
            sales_channel_view=self.view,
            remote_product=self.remote_product_processing,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.assign_failed = SalesChannelViewAssign.objects.create(
            product=self.product_failed,
            sales_channel_view=self.view,
            remote_product=self.remote_product_failed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.assign_without_remote = SalesChannelViewAssign.objects.create(
            product=baker.make(
                "products.Product",
                type="SIMPLE",
                multi_tenant_company=self.multi_tenant_company,
            ),
            sales_channel_view=self.view,
            remote_product=None,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_filter_by_status_completed(self):
        queryset = SalesChannelViewAssign.objects.filter_by_status(
            status=RemoteProduct.STATUS_COMPLETED,
        ).order_by("id")
        self.assertListEqual(
            list(queryset),
            [self.assign_completed],
        )

    def test_filter_by_status_processing(self):
        queryset = SalesChannelViewAssign.objects.filter_by_status(
            status=RemoteProduct.STATUS_PROCESSING,
        ).order_by("id")
        self.assertListEqual(
            list(queryset),
            [self.assign_processing],
        )

    def test_filter_by_status_failed(self):
        queryset = SalesChannelViewAssign.objects.filter_by_status(
            status=RemoteProduct.STATUS_FAILED,
        ).order_by("id")
        self.assertListEqual(
            list(queryset),
            [self.assign_failed],
        )

    def test_filter_by_status_created_excludes_failed(self):
        queryset = SalesChannelViewAssign.objects.filter_by_status(
            status=SalesChannelViewAssign.STATUS_CREATED,
        ).order_by("id")
        self.assertNotIn(self.assign_failed, list(queryset))

    def test_filter_by_status_unknown_returns_empty(self):
        queryset = SalesChannelViewAssign.objects.filter_by_status(status="UNKNOWN")
        self.assertEqual(queryset.count(), 0)
