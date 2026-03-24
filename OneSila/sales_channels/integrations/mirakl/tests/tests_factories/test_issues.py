from datetime import datetime
from unittest.mock import Mock, patch

from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.sales_channels import MiraklProductIssuesFetchFactory
from sales_channels.integrations.mirakl.models import (
    MiraklEanCode,
    MiraklProduct,
    MiraklProductIssue,
    MiraklSalesChannel,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductIssuesFetchFactoryTests(DisableMiraklConnectionMixin, TestCase):
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
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="shopSku1",
            syncing_current_percentage=100,
        )
        baker.make(
            MiraklEanCode,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            ean_code="EAN1",
        )
        self.view_be = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="BE",
            name="Belgium",
        )
        self.view_fr = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="FR",
            name="France",
        )
        self.view_us = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="US",
            name="United States",
        )
        self.view_ca = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CA",
            name="Canada",
        )

    def _response(self, *, status_code: int, payload=None) -> Mock:
        response = Mock(status_code=status_code)
        response.json = Mock(return_value=payload)
        return response

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.timezone.now")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.MiraklProductIssuesFetchFactory._request")
    def test_full_sync_creates_expected_issue_rows_and_attaches_views(self, request_mock, now_mock):
        now_mock.return_value = timezone.make_aware(datetime(2026, 3, 19, 10, 0, 0))
        request_mock.return_value = self._response(
            status_code=200,
            payload=[
                {
                    "errors": [
                        {
                            "channels": ["BE", "FR"],
                            "code": "MCM-04012",
                            "message": "The product has been rejected by the operator temporarily.",
                            "rejection_details": {
                                "message": "This product is obsolete",
                                "reason_code": "2",
                                "reason_label": "The product does not fit the targeted audience",
                            },
                        },
                        {
                            "channels": ["US", "CA"],
                            "code": "MCM-04012",
                            "message": "The operator has requested changes to your product data.",
                            "rejection_details": {
                                "message": "The description in English is not detailed enough.",
                                "reason_code": "5",
                                "reason_label": "A better description is required",
                            },
                        },
                        {
                            "code": "MCM-0L000",
                            "message": "The product has not been synchronized yet.",
                        },
                        {
                            "code": "MCM-04000",
                            "integration_details": [
                                {
                                    "attribute_code": "color",
                                    "code": "WARNING",
                                    "message": "is not mapped",
                                }
                            ],
                            "message": "The product integration contains errors.",
                        },
                    ],
                    "unique_identifiers": [
                        {"code": "EAN", "value": "EAN1"},
                        {"code": "EAN", "value": "EAN2"},
                        {"code": "ISBN", "value": "ISBN1"},
                    ],
                    "warnings": [
                        {
                            "attribute_code": "mainImageLarge",
                            "code": "MCM-05000",
                            "message": "The 'mainImageLarge' attribute is required.",
                        }
                    ],
                }
            ],
        )

        result = MiraklProductIssuesFetchFactory(
            sales_channel=self.sales_channel,
            mode=MiraklProductIssuesFetchFactory.MODE_FULL,
        ).run()

        self.assertFalse(result["skipped"])
        self.assertEqual(result["products"], 1)
        self.assertEqual(MiraklProductIssue.objects.filter(remote_product=self.remote_product).count(), 5)

        rejection_issue = MiraklProductIssue.objects.get(code="2")
        self.assertEqual(rejection_issue.main_code, "MCM-04012")
        self.assertTrue(rejection_issue.is_rejected)
        self.assertEqual(
            rejection_issue.message,
            "The product has been rejected by the operator temporarily. | This product is obsolete",
        )
        self.assertEqual(
            list(rejection_issue.views.order_by("remote_id").values_list("remote_id", flat=True)),
            ["BE", "FR"],
        )

        second_rejection = MiraklProductIssue.objects.get(code="5")
        self.assertEqual(
            list(second_rejection.views.order_by("remote_id").values_list("remote_id", flat=True)),
            ["CA", "US"],
        )

        plain_error = MiraklProductIssue.objects.get(code="MCM-0L000")
        self.assertEqual(plain_error.main_code, "MCM-0L000")
        self.assertEqual(plain_error.severity, "ERROR")
        self.assertFalse(plain_error.views.exists())

        integration_issue = MiraklProductIssue.objects.get(main_code="MCM-04000")
        self.assertEqual(integration_issue.code, "WARNING")
        self.assertEqual(integration_issue.attribute_code, "color")
        self.assertEqual(
            integration_issue.message,
            "The product integration contains errors. | is not mapped",
        )

        warning_issue = MiraklProductIssue.objects.get(code="MCM-05000")
        self.assertEqual(warning_issue.severity, "WARNING")
        self.assertEqual(warning_issue.attribute_code, "mainImageLarge")
        self.assertFalse(warning_issue.views.exists())
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_APPROVAL_REJECTED)

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.MiraklProductIssuesFetchFactory._request")
    def test_differential_sync_keeps_existing_issues_on_204(self, request_mock):
        self.sales_channel.last_differential_issues_fetch = timezone.make_aware(
            datetime(2026, 3, 19, 9, 0, 0)
        )
        self.sales_channel.save(update_fields=["last_differential_issues_fetch"])
        existing_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="OLD",
            code="OLD",
            severity="ERROR",
        )
        boundary = timezone.make_aware(datetime(2026, 3, 19, 10, 0, 0))
        request_mock.return_value = self._response(status_code=204, payload=None)

        with patch(
            "sales_channels.integrations.mirakl.factories.sales_channels.issues.timezone.now",
            return_value=boundary,
        ):
            MiraklProductIssuesFetchFactory(
                sales_channel=self.sales_channel,
                mode=MiraklProductIssuesFetchFactory.MODE_DIFFERENTIAL,
            ).run()

        self.assertTrue(MiraklProductIssue.objects.filter(id=existing_issue.id).exists())
        self.sales_channel.refresh_from_db()
        self.assertEqual(self.sales_channel.last_differential_issues_fetch, boundary)

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.MiraklProductIssuesFetchFactory._request")
    def test_full_sync_clears_existing_issues_on_204(self, request_mock):
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="OLD",
            code="OLD",
            severity="ERROR",
            raw_data={"source": "error"},
        )
        self.remote_product.refresh_status(commit=True)
        boundary = timezone.make_aware(datetime(2026, 3, 19, 11, 0, 0))
        request_mock.return_value = self._response(status_code=204, payload=None)

        with patch(
            "sales_channels.integrations.mirakl.factories.sales_channels.issues.timezone.now",
            return_value=boundary,
        ):
            MiraklProductIssuesFetchFactory(
                sales_channel=self.sales_channel,
                mode=MiraklProductIssuesFetchFactory.MODE_FULL,
            ).run()

        self.assertFalse(MiraklProductIssue.objects.filter(remote_product=self.remote_product).exists())
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_COMPLETED)
        self.sales_channel.refresh_from_db()
        self.assertEqual(self.sales_channel.last_full_issues_fetch, boundary)
        self.assertEqual(self.sales_channel.last_differential_issues_fetch, boundary)

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.MiraklProductIssuesFetchFactory._request")
    def test_full_sync_204_keeps_transformation_report_issues(self, request_mock):
        api_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="OLD",
            code="OLD",
            severity="ERROR",
            raw_data={"source": "error"},
        )
        report_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="1000",
            code="1000",
            severity="ERROR",
            raw_data={"source": "transformation_error_report_error"},
        )
        request_mock.return_value = self._response(status_code=204, payload=None)

        MiraklProductIssuesFetchFactory(
            sales_channel=self.sales_channel,
            mode=MiraklProductIssuesFetchFactory.MODE_FULL,
        ).run()

        self.assertFalse(MiraklProductIssue.objects.filter(id=api_issue.id).exists())
        self.assertTrue(MiraklProductIssue.objects.filter(id=report_issue.id).exists())

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.issues.MiraklProductIssuesFetchFactory._request")
    def test_api_sync_for_product_keeps_existing_transformation_report_issues(self, request_mock):
        report_issue = baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            main_code="1000",
            code="1000",
            severity="ERROR",
            raw_data={"source": "transformation_error_report_error"},
        )
        request_mock.return_value = self._response(
            status_code=200,
            payload=[
                {
                    "warnings": [
                        {
                            "code": "MCM-05000",
                            "message": "The 'mainImageLarge' attribute is required.",
                        }
                    ],
                    "unique_identifiers": [
                        {"code": "SKU", "value": "shopSku1"},
                    ],
                }
            ],
        )

        MiraklProductIssuesFetchFactory(
            sales_channel=self.sales_channel,
            mode=MiraklProductIssuesFetchFactory.MODE_FULL,
        ).run()

        self.assertTrue(MiraklProductIssue.objects.filter(id=report_issue.id).exists())
        self.assertTrue(
            MiraklProductIssue.objects.filter(
                remote_product=self.remote_product,
                code="MCM-05000",
                raw_data__source="warning",
            ).exists()
        )
