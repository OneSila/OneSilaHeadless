from django.core.exceptions import ValidationError

from core.tests import TestCase
from media.models import DocumentType
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinDocumentType,
    SheinSalesChannel,
)


class SheinDocumentTypeModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein-doc-types.test",
            remote_id="SHEIN-1",
        )
        self.other_sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein-doc-types-other.test",
            remote_id="SHEIN-2",
        )

    def test_save_accepts_existing_category_remote_ids_for_same_channel(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="100",
            name="Category 100",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="101",
            name="Category 101",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERTIFICATE_OF_ANALYSIS",
            name="Certificate of Analysis",
            required_categories=["100"],
            optional_categories=[{"remote_id": "101"}],
        )

        self.assertEqual(document_type.required_categories, ["100"])
        self.assertEqual(document_type.optional_categories, ["101"])

    def test_save_rejects_unknown_category_remote_ids(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="100",
            name="Category 100",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            SheinDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="CERTIFICATE_OF_CONFORMITY",
                required_categories=["999"],
                optional_categories=[],
            )

    def test_save_rejects_category_remote_ids_from_other_sales_channel(self):
        SheinCategory.objects.create(
            sales_channel=self.other_sales_channel,
            remote_id="200",
            name="Other Channel Category",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            SheinDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="DECLARATION_OF_CONFORMITY",
                required_categories=["200"],
                optional_categories=[],
            )

    def test_save_rejects_overlapping_required_and_optional_categories(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="300",
            name="Category 300",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            SheinDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="INSTRUCTIONS_FOR_USE",
                required_categories=["300"],
                optional_categories=["300"],
            )

    def test_save_rejects_mapping_internal_document_type(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="400",
            name="Category 400",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        internal_document_type, _ = DocumentType.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            name=DocumentType.INTERNAL_NAME,
            code=DocumentType.INTERNAL_CODE,
            description=DocumentType.INTERNAL_DESCRIPTION,
        )

        with self.assertRaises(ValidationError):
            SheinDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=internal_document_type,
                remote_id="OTHER_SAFETY_DOCUMENTS",
                required_categories=["400"],
                optional_categories=[],
            )

    def test_add_required_category_appends_without_duplicates(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="500",
            name="Category 500",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT_A",
            required_categories=[],
            optional_categories=[],
        )

        first_changed = document_type.add_required_category(category_remote_id="500")
        second_changed = document_type.add_required_category(category_remote_id="500")
        document_type.refresh_from_db()

        self.assertTrue(first_changed)
        self.assertFalse(second_changed)
        self.assertEqual(document_type.required_categories, ["500"])
        self.assertEqual(document_type.optional_categories, [])

    def test_add_optional_category_moves_value_out_of_required(self):
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="600",
            name="Category 600",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT_B",
            required_categories=["600"],
            optional_categories=[],
        )

        changed = document_type.add_optional_category(category_remote_id="600")
        document_type.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(document_type.required_categories, [])
        self.assertEqual(document_type.optional_categories, ["600"])
