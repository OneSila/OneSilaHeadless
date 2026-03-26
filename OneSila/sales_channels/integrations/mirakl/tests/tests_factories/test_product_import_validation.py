from io import BytesIO

from django.core.files.base import ContentFile
from model_bakery import baker
from openpyxl import Workbook

from core.tests import TestCase
from sales_channels.exceptions import (
    MiraklImportInvalidFileLayoutError,
    MiraklImportInvalidFileTypeError,
    MiraklImportMissingFilesError,
)
from sales_channels.integrations.mirakl.factories.imports.products import MiraklProductsImportProcessor
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelImportExportFile,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductsImportValidationTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
            active=True,
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_PRODUCTS,
            skip_broken_records=True,
        )

    def _build_workbook_bytes(self, *, second_row=None):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(["Column A", "Column B"])
        if second_row is not None:
            worksheet.append(second_row)

        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        return stream.getvalue()

    def _create_export_file(self, *, filename, content):
        export_file = baker.make(
            MiraklSalesChannelImportExportFile,
            multi_tenant_company=self.multi_tenant_company,
            import_process=self.import_process,
        )
        export_file.file.save(filename, ContentFile(content), save=True)
        return export_file

    def test_validate_requires_at_least_one_file(self):
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportMissingFilesError):
            processor.validate()

    def test_validate_rejects_non_xlsx_files(self):
        self._create_export_file(filename="export.csv", content=b"not-an-xlsx")
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportInvalidFileTypeError):
            processor.validate()

    def test_validate_rejects_missing_second_row(self):
        self._create_export_file(
            filename="export.xlsx",
            content=self._build_workbook_bytes(second_row=None),
        )
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportInvalidFileLayoutError):
            processor.validate()

    def test_validate_rejects_unknown_property_codes(self):
        self._create_export_file(
            filename="export.xlsx",
            content=self._build_workbook_bytes(second_row=["unknown_code", "another_code"]),
        )
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportInvalidFileLayoutError):
            processor.validate()

    def test_validate_accepts_known_property_codes(self):
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_category",
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="shop_sku",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
        )
        self._create_export_file(
            filename="export.xlsx",
            content=self._build_workbook_bytes(second_row=["product_category", "shop_sku"]),
        )
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        processor.validate()

    def test_validate_requires_product_sku_property_on_channel(self):
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_category",
        )
        self._create_export_file(
            filename="export.xlsx",
            content=self._build_workbook_bytes(second_row=["product_category"]),
        )
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportInvalidFileLayoutError):
            processor.validate()

    def test_validate_requires_product_sku_column_in_file(self):
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="shop_sku",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_category",
        )
        self._create_export_file(
            filename="export.xlsx",
            content=self._build_workbook_bytes(second_row=["product_category"]),
        )
        processor = MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with self.assertRaises(MiraklImportInvalidFileLayoutError):
            processor.validate()
