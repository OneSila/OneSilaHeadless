from datetime import timedelta
from unittest.mock import Mock, patch

from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklImportStatusSyncFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklImportStatusSyncFactoryTests(DisableMiraklConnectionMixin, TestCase):
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

    def test_run_updates_only_submitted_feeds_with_remote_id_and_downloads_reports(self):
        submitted_feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
            remote_id="2008",
            product_remote_id="2008",
        )
        ignored_feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_PENDING,
            remote_id="2009",
        )
        tracking = {
            "import_id": 2008,
            "import_status": "COMPLETE",
            "reason_status": "Processed",
            "date_created": "2019-04-05T13:13:06Z",
            "shop_id": 2000,
            "conversion_type": "AI_CONVERTER",
            "conversion_options": {
                "ai_enrichment": {"status": "ENABLED"},
                "ai_rewrite": {"status": "DISABLED"},
            },
            "integration_details": {
                "invalid_products": 2,
                "products_not_accepted_in_time": 1,
                "products_not_synchronized_in_time": 3,
                "products_reimported": 4,
                "products_successfully_synchronized": 5,
                "products_with_synchronization_issues": 6,
                "products_with_wrong_identifiers": 7,
                "rejected_products": 8,
            },
            "has_error_report": True,
            "has_new_product_report": True,
            "has_transformation_error_report": True,
            "has_transformed_file": True,
            "transform_lines_read": 2,
            "transform_lines_in_success": 1,
            "transform_lines_in_error": 1,
            "transform_lines_with_warning": 0,
        }
        download_response = Mock(
            status_code=200,
            content=b"report-content",
            headers={"Content-Type": "text/csv"},
        )

        with patch.object(
            MiraklImportStatusSyncFactory,
            "mirakl_paginated_get",
            return_value=[tracking],
        ) as paginated_get_mock, patch.object(
            MiraklImportStatusSyncFactory,
            "_request",
            side_effect=[download_response, download_response, download_response, download_response],
        ):
            refreshed = MiraklImportStatusSyncFactory(sales_channel=self.sales_channel).run()

        paginated_get_mock.assert_called_once()
        self.assertEqual(len(refreshed), 1)
        submitted_feed.refresh_from_db()
        ignored_feed.refresh_from_db()

        self.assertEqual(submitted_feed.status, MiraklSalesChannelFeed.STATUS_PARTIAL)
        self.assertEqual(submitted_feed.import_status, "COMPLETE")
        self.assertEqual(submitted_feed.conversion_type, "AI_CONVERTER")
        self.assertTrue(submitted_feed.conversion_options_ai_enrichment_enabled)
        self.assertFalse(submitted_feed.conversion_options_ai_rewrite_enabled)
        self.assertEqual(submitted_feed.integration_details_invalid_products, 2)
        self.assertEqual(submitted_feed.integration_details_rejected_products, 8)
        self.assertTrue(bool(submitted_feed.error_report_file))
        self.assertTrue(bool(submitted_feed.new_product_report_file))
        self.assertTrue(bool(submitted_feed.transformed_file))
        self.assertTrue(bool(submitted_feed.transformation_error_report_file))
        self.assertIsNotNone(self.sales_channel.last_product_imports_request_date)
        self.assertEqual(ignored_feed.status, MiraklSalesChannelFeed.STATUS_PENDING)

    def test_run_uses_last_request_date_when_present(self):
        boundary = timezone.now() - timedelta(minutes=30)
        self.sales_channel.last_product_imports_request_date = boundary
        self.sales_channel.save(update_fields=["last_product_imports_request_date"])

        with patch.object(
            MiraklImportStatusSyncFactory,
            "mirakl_paginated_get",
            return_value=[],
        ) as paginated_get_mock:
            MiraklImportStatusSyncFactory(sales_channel=self.sales_channel).run()

        self.assertIn("last_request_date", paginated_get_mock.call_args.kwargs["params"])
