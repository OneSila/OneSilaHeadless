from io import BytesIO

from django.core.files.base import ContentFile
from model_bakery import baker
from openpyxl import Workbook

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklTransformationErrorReportIssueSyncFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductIssue,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklTransformationErrorReportIssueSyncFactoryTests(DisableMiraklConnectionMixin, TestCase):
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
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
            name="Default",
        )
        self.product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.sku_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_id",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
        )
        MiraklProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=self.product_type,
            remote_property=self.sku_property,
        )
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="ILFD4043XS+5029+1479-58",
        )
        self.feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            product_type=self.product_type,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_PARTIAL,
        )
        baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
            payload_data=[
                {
                    "product_id": "ILFD4043XS+5029+1479-58",
                    "ean": "5056863153211",
                    "product_category": "Toys/Dress Up & Role Play",
                }
            ],
        )

    def _build_workbook_bytes(self) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(
            [
                "line number",
                "errors",
                "warnings",
                "product_category",
                "parent_product_id",
                "product_id",
                "ean",
            ]
        )
        worksheet.append(
            [
                3,
                "1000|The attribute 'main_image' (Main Image) is required,1001|Brand is required",
                "3004|Description should be shorter",
                "Toys/Dress Up & Role Play",
                "ILFD4043+5029+1479-58",
                "ILFD4043XS+5029+1479-58",
                "5056863153211",
            ]
        )

        buffer = BytesIO()
        workbook.save(buffer)
        workbook.close()
        return buffer.getvalue()

    def test_run_parses_xlsx_and_upserts_issues_for_feed_rows(self):
        self.feed.transformation_error_report_file.save(
            "mirakl-transform-errors.xlsx",
            ContentFile(self._build_workbook_bytes()),
            save=True,
        )

        synced_issues = MiraklTransformationErrorReportIssueSyncFactory(feed=self.feed).run()

        self.assertEqual(synced_issues, 3)
        self.assertEqual(MiraklProductIssue.objects.filter(remote_product=self.remote_product).count(), 3)

        error_issue = MiraklProductIssue.objects.get(
            remote_product=self.remote_product,
            code="1000",
        )
        self.assertEqual(error_issue.main_code, "1000")
        self.assertEqual(error_issue.message, "The attribute 'main_image' (Main Image) is required")
        self.assertEqual(error_issue.severity, "ERROR")
        self.assertEqual(error_issue.raw_data["source"], "transformation_error_report_error")
        self.assertEqual(error_issue.raw_data["line_number"], "3")
        self.assertEqual(list(error_issue.views.values_list("id", flat=True)), [self.view.id])

        warning_issue = MiraklProductIssue.objects.get(
            remote_product=self.remote_product,
            code="3004",
        )
        self.assertEqual(warning_issue.severity, "WARNING")
        self.assertEqual(warning_issue.raw_data["source"], "transformation_error_report_warning")
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_APPROVAL_REJECTED)
