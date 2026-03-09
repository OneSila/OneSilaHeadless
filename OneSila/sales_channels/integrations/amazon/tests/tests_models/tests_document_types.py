from django.core.exceptions import ValidationError

from core.tests import TestCase
from media.models import DocumentType
from sales_channels.integrations.amazon.models import (
    AmazonBrowseNode,
    AmazonDocumentType,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)


class AmazonDocumentTypeModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="amazon-doc-types.test",
            remote_id="SELLER-1",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="A1F83G8C2ARO7P",
            name="UK",
        )

    def test_save_accepts_existing_browse_node_remote_ids(self):
        AmazonBrowseNode.objects.create(
            remote_id="100",
            marketplace_id=self.view.remote_id,
            name="Node 100",
        )
        AmazonBrowseNode.objects.create(
            remote_id="101",
            marketplace_id=self.view.remote_id,
            name="Node 101",
        )

        document_type = AmazonDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERTIFICATE_OF_ANALYSIS",
            name="Certificate of Analysis",
            required_categories=["100"],
            optional_categories=[{"remote_id": "101"}],
        )

        self.assertEqual(document_type.required_categories, ["100"])
        self.assertEqual(document_type.optional_categories, ["101"])

    def test_save_rejects_unknown_browse_node_remote_ids(self):
        AmazonBrowseNode.objects.create(
            remote_id="100",
            marketplace_id=self.view.remote_id,
            name="Node 100",
        )

        with self.assertRaises(ValidationError):
            AmazonDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="CERTIFICATE_OF_CONFORMITY",
                required_categories=["999"],
                optional_categories=[],
            )

    def test_save_rejects_browse_node_remote_ids_outside_channel_marketplaces(self):
        AmazonBrowseNode.objects.create(
            remote_id="200",
            marketplace_id="ATVPDKIKX0DER",
            name="Other marketplace node",
        )

        with self.assertRaises(ValidationError):
            AmazonDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="DECLARATION_OF_CONFORMITY",
                required_categories=["200"],
                optional_categories=[],
            )

    def test_save_rejects_overlapping_required_and_optional_categories(self):
        AmazonBrowseNode.objects.create(
            remote_id="300",
            marketplace_id=self.view.remote_id,
            name="Node 300",
        )

        with self.assertRaises(ValidationError):
            AmazonDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="INSTRUCTIONS_FOR_USE",
                required_categories=["300"],
                optional_categories=["300"],
            )

    def test_save_rejects_mapping_internal_document_type(self):
        AmazonBrowseNode.objects.create(
            remote_id="400",
            marketplace_id=self.view.remote_id,
            name="Node 400",
        )
        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            name=DocumentType.INTERNAL_NAME,
            code=DocumentType.INTERNAL_CODE,
            description=DocumentType.INTERNAL_DESCRIPTION,
        )

        with self.assertRaises(ValidationError):
            AmazonDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=internal_document_type,
                remote_id="OTHER_SAFETY_DOCUMENTS",
                required_categories=["400"],
                optional_categories=[],
            )

    def test_save_rejects_duplicate_local_mapping_per_sales_channel(self):
        local_document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Compliance Document",
            code="COMPLIANCE_DOCUMENT",
        )

        AmazonDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id="USER_GUIDE",
            required_categories=[],
            optional_categories=[],
        )

        with self.assertRaises(ValidationError):
            AmazonDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=local_document_type,
                remote_id="USER_MANUAL",
                required_categories=[],
                optional_categories=[],
            )
