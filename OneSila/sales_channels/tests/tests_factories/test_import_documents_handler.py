from types import SimpleNamespace
from unittest.mock import MagicMock

from core.tests import TestCase
from media.models import Media, MediaProductThrough
from model_bakery import baker
from products.models import Product
from sales_channels.factories.imports.imports import SalesChannelImportMixin
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.models import RemoteDocument, RemoteDocumentProductAssociation, RemoteProduct
from sales_channels.models.imports import SalesChannelImport


class DummySalesChannelImportProcessor(SalesChannelImportMixin):
    def get_api(self):
        return MagicMock()

    def get_total_instances(self):
        return 0

    def get_properties_data(self):
        return []

    def get_select_values_data(self):
        return []

    def get_rules_data(self):
        return []

    def get_product_data(self, import_instance):
        return {}


class SalesChannelImportMixinDocumentHandlerTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://documents-import-handler.test",
        )
        self.import_process = SalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.product = baker.make(
            Product,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
        )

    def test_handle_documents_skips_when_integration_has_documents_is_disabled(self):
        processor = DummySalesChannelImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.remote_documentproductassociation_class = RemoteDocumentProductAssociation

        import_instance = SimpleNamespace(
            documents=[{"document_url": "https://example.com/a.pdf"}],
            documents_associations_instances=[self.media_through],
            data={"__document_index_to_remote_id": {"0": "DOC-001"}},
            remote_instance=self.remote_product,
        )

        processor.handle_documents(import_instance=import_instance)

        self.assertFalse(RemoteDocument.objects.exists())
        self.assertFalse(RemoteDocumentProductAssociation.objects.exists())

    def test_handle_documents_creates_remote_document_and_association(self):
        processor = DummySalesChannelImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.integration_has_documents = True
        processor.remote_document_class = RemoteDocument
        processor.remote_documentproductassociation_class = RemoteDocumentProductAssociation

        import_instance = SimpleNamespace(
            documents=[{"document_url": "https://example.com/a.pdf"}],
            documents_associations_instances=[self.media_through],
            data={"__document_index_to_remote_id": {"0": "DOC-001"}},
            remote_instance=self.remote_product,
        )

        processor.handle_documents(import_instance=import_instance)
        processor.handle_documents(import_instance=import_instance)

        self.assertEqual(RemoteDocument.objects.count(), 1)
        self.assertEqual(RemoteDocumentProductAssociation.objects.count(), 1)

        remote_document = RemoteDocument.objects.get()
        self.assertEqual(remote_document.local_instance_id, self.media.id)
        self.assertEqual(remote_document.sales_channel_id, self.sales_channel.id)
        self.assertEqual(remote_document.remote_id, "DOC-001")

        association = RemoteDocumentProductAssociation.objects.get()
        self.assertEqual(association.local_instance_id, self.media_through.id)
        self.assertEqual(association.remote_product_id, self.remote_product.id)
        self.assertEqual(association.remote_document_id, remote_document.id)
        self.assertEqual(association.remote_id, "DOC-001")

    def test_handle_documents_uses_existing_remote_document_when_integration_has_documents_is_disabled(self):
        processor = DummySalesChannelImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.remote_documentproductassociation_class = RemoteDocumentProductAssociation

        existing_remote_document = RemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_id="DOC-EXISTING",
        )

        import_instance = SimpleNamespace(
            documents=[{"document_url": "https://example.com/a.pdf"}],
            documents_associations_instances=[self.media_through],
            data={"__document_index_to_remote_id": {"0": "DOC-EXISTING"}},
            remote_instance=self.remote_product,
        )

        processor.handle_documents(import_instance=import_instance)

        self.assertEqual(RemoteDocument.objects.count(), 1)
        association = RemoteDocumentProductAssociation.objects.get()
        self.assertEqual(association.remote_document_id, existing_remote_document.id)
        self.assertEqual(association.remote_id, "DOC-EXISTING")
