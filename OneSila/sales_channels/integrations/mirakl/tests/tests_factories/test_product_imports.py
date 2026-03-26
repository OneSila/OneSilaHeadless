from io import BytesIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from model_bakery import baker
from openpyxl import Workbook

from core.tests import TestCase
from products.models import ConfigurableVariation, Product
from properties.models import ProductProperty, Property, PropertySelectValue
from sales_channels.integrations.mirakl.factories.imports.products import MiraklProductsImportProcessor
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelImportExportFile,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductsImportProcessorTests(DisableMiraklConnectionMixin, TestCase):
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
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="UK",
            name="United Kingdom",
            url="https://shop.example.com",
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_PRODUCTS,
            skip_broken_records=True,
        )

    def _build_workbook_bytes(self, *, codes, rows, error_rows=None):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append([f"Label {index}" for index in range(1, len(codes) + 1)])
        worksheet.append(codes)
        for row in rows:
            worksheet.append(row)

        if error_rows:
            error_worksheet = workbook.create_sheet(title="Error Details")
            error_worksheet.append(
                [
                    "line-number",
                    "provider-unique-identifier",
                    "channels",
                    "attribute-label",
                    "attribute-codes",
                    "error-code",
                    "error-message",
                ]
            )
            for error_row in error_rows:
                error_worksheet.append(error_row)

        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        return stream.getvalue()

    def _create_export_file(self, *, codes, rows, error_rows=None):
        export_file = baker.make(
            MiraklSalesChannelImportExportFile,
            multi_tenant_company=self.multi_tenant_company,
            import_process=self.import_process,
        )
        export_file.file.save(
            "mirakl-import.xlsx",
            ContentFile(self._build_workbook_bytes(codes=codes, rows=rows, error_rows=error_rows)),
            save=True,
        )
        return export_file

    def _create_basic_properties(self):
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
            code="product_title",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_category",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_CATEGORY,
        )

    @patch.object(MiraklProductsImportProcessor, "mirakl_paginated_get")
    def test_run_import_uses_of21_fallbacks_and_creates_category_assign(self, mirakl_paginated_get_mock):
        self._create_basic_properties()
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            name="Category",
            is_leaf=True,
        )
        self._create_export_file(
            codes=["shop_sku", "product_title", "product_category"],
            rows=[["SELLER-1", "", ""]],
        )
        mirakl_paginated_get_mock.return_value = [
            {
                "shop_sku": "SELLER-1",
                "product_sku": "REMOTE-1",
                "product_title": "Offer Title",
                "description": "Offer description",
                "internal_description": "Short description",
                "category_code": "CAT-1",
                "currency_iso_code": "GBP",
                "price": 12.5,
                "active": True,
                "channels": ["UK"],
            }
        ]

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        product = Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku="SELLER-1")
        remote_product = MiraklProduct.objects.get(local_instance=product, sales_channel=self.sales_channel)
        self.assertEqual(product.name, "Offer Title")
        self.assertEqual(remote_product.remote_sku, "REMOTE-1")
        self.assertTrue(
            MiraklProductCategory.objects.filter(
                product=product,
                sales_channel=self.sales_channel,
                remote_id="CAT-1",
            ).exists()
        )
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                product=product,
                sales_channel_view=self.view,
                remote_product=remote_product,
            ).exists()
        )
        self.assertTrue(
            MiraklPrice.objects.filter(
                remote_product=remote_product,
                sales_channel=self.sales_channel,
            ).exists()
        )

    @patch.object(MiraklProductsImportProcessor, "mirakl_paginated_get")
    def test_run_import_prefers_of21_category_code_over_file_category_label(self, mirakl_paginated_get_mock):
        self._create_basic_properties()
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-OF21",
            name="Dress Up & Role Play",
            is_leaf=True,
        )
        self._create_export_file(
            codes=["shop_sku", "product_title", "product_category"],
            rows=[["SELLER-2", "Fancy Dress Item", "Toys/Dress Up & Role Play"]],
        )
        mirakl_paginated_get_mock.return_value = [
            {
                "shop_sku": "SELLER-2",
                "product_sku": "REMOTE-2",
                "product_title": "Fancy Dress Item",
                "category_code": "CAT-OF21",
                "channels": ["UK"],
                "active": True,
            }
        ]

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        product = Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku="SELLER-2")
        self.assertTrue(
            MiraklProductCategory.objects.filter(
                product=product,
                sales_channel=self.sales_channel,
                remote_id="CAT-OF21",
            ).exists()
        )

    @patch.object(MiraklProductsImportProcessor, "mirakl_paginated_get")
    def test_run_import_builds_configurable_parent_and_variation_remote_links(self, mirakl_paginated_get_mock):
        self._create_basic_properties()
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="parent_sku",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
        )
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-2",
            name="Category 2",
            is_leaf=True,
        )
        self._create_export_file(
            codes=["shop_sku", "parent_sku", "product_title", "product_category"],
            rows=[["SELLER-CHILD", "PARENT-1", "Variant Title", "CAT-2"]],
        )
        mirakl_paginated_get_mock.return_value = [
            {
                "shop_sku": "SELLER-CHILD",
                "product_sku": "REMOTE-CHILD",
                "product_title": "Variant Title",
                "category_code": "CAT-2",
                "channels": ["UK"],
                "active": True,
            }
        ]

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        parent = Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku="PARENT-1")
        child = Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku="SELLER-CHILD")
        parent_remote = MiraklProduct.objects.get(local_instance=parent, sales_channel=self.sales_channel)
        child_remote = MiraklProduct.objects.get(local_instance=child, sales_channel=self.sales_channel)

        self.assertTrue(parent.is_configurable())
        self.assertTrue(child.is_simple())
        self.assertTrue(
            ConfigurableVariation.objects.filter(parent=parent, variation=child).exists()
        )
        self.assertEqual(parent_remote.remote_sku, "PARENT-1")
        self.assertEqual(child_remote.remote_sku, "REMOTE-CHILD")
        self.assertEqual(child_remote.remote_parent_product_id, parent_remote.id)
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                product=parent,
                sales_channel_view=self.view,
                remote_product=parent_remote,
            ).exists()
        )
        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                product=child,
                sales_channel_view=self.view,
            ).exists()
        )
        self.assertTrue(
            MiraklProductCategory.objects.filter(
                product=parent,
                sales_channel=self.sales_channel,
                remote_id="CAT-2",
            ).exists()
        )
        self.assertTrue(
            MiraklProductCategory.objects.filter(
                product=child,
                sales_channel=self.sales_channel,
                remote_id="CAT-2",
            ).exists()
        )

    @patch.object(MiraklProductsImportProcessor, "mirakl_paginated_get", return_value=[])
    def test_run_import_maps_select_values_by_remote_value(self, _mirakl_paginated_get_mock):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            name="Brand",
            internal_name="brand",
            type=Property.TYPES.SELECT,
        )
        local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
            value="Acme",
        )
        baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="shop_sku",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
        )
        remote_brand = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="product_brand",
            local_instance=local_property,
            type=Property.TYPES.SELECT,
        )
        baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_brand,
            local_instance=local_value,
            code="ACME_CODE",
            value="Acme",
        )
        self._create_export_file(
            codes=["shop_sku", "product_brand"],
            rows=[["SELLER-2", "Acme"]],
        )

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        product = Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku="SELLER-2")
        product_property = ProductProperty.objects.get(product=product, property=local_property)
        self.assertEqual(product_property.value_select_id, local_value.id)

    @patch.object(MiraklProductsImportProcessor, "mirakl_paginated_get")
    def test_run_import_creates_issues_from_error_details_sheet(self, mirakl_paginated_get_mock):
        self._create_basic_properties()
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-3",
            name="Category 3",
            is_leaf=True,
        )
        self._create_export_file(
            codes=["shop_sku", "product_title", "product_category"],
            rows=[["SELLER-3", "Offer 3", "CAT-3"]],
            error_rows=[
                [
                    3,
                    "SELLER-3",
                    "UK",
                    "",
                    "",
                    "VARIANT_DESCRIPTION_MISMATCH : Description is different across variants",
                    "Auto Validation Failed: Descriptions must be identical for grouped products",
                ]
            ],
        )
        mirakl_paginated_get_mock.return_value = [
            {
                "shop_sku": "SELLER-3",
                "product_sku": "REMOTE-3",
                "product_title": "Offer 3",
                "category_code": "CAT-3",
                "channels": ["UK"],
                "active": True,
            }
        ]

        MiraklProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        ).run()

        remote_product = MiraklProduct.objects.get(
            sales_channel=self.sales_channel,
            remote_sku="REMOTE-3",
        )
        issue = remote_product.issues.get()
        self.assertEqual(issue.code, "VARIANT_DESCRIPTION_MISMATCH")
        self.assertEqual(issue.severity, "ERROR")
        self.assertEqual(
            issue.raw_data["source"],
            MiraklProductsImportProcessor.ISSUE_SOURCE_ERROR_DETAILS,
        )
        self.assertEqual(list(issue.views.values_list("remote_id", flat=True)), ["UK"])
