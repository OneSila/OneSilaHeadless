from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from django.core.files.base import ContentFile
from model_bakery import baker

from core.tests import TestCase
from integrations.models import IntegrationLog
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableVariation, Product
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.shein.factories.products import (
    SheinDocumentThroughProductUpdateFactory,
    SheinProductCreateFactory,
    SheinProductExternalDocumentsFactory,
    SheinRemoteDocumentCreateFactory,
    SheinRemoteDocumentUpdateFactory,
)
from sales_channels.integrations.shein.helpers.certificate_types import (
    PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER,
    RESOLVED_EXTERNAL_DOCUMENTS_IDENTIFIER,
)
from sales_channels.integrations.shein.models import (
    SheinDocument,
    SheinDocumentThroughProduct,
    SheinDocumentType,
    SheinProduct,
    SheinSalesChannel,
)
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


class SheinDocumentPushFactoriesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="DOC-SKU-1",
        )
        self.remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="DOC-SKU-1",
            remote_id="SPU-1",
            spu_name="SPU-1",
            skc_name="SKC-1",
        )

        self.local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="Test Certificate",
        )
        self.remote_document_type = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_document_type,
            remote_id="340",
            name="UK Agent",
            translated_name="UK Agent",
        )

        self.media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=self.local_document_type,
        )
        self.media.file.save("certificate.pdf", ContentFile(b"%PDF-1.4 certificate"), save=True)
        self.media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
            sort_order=1,
        )

    @patch.object(SheinRemoteDocumentCreateFactory, "save_or_update_certificate_pool")
    @patch.object(SheinRemoteDocumentCreateFactory, "upload_certificate_file")
    def test_remote_document_create_uploads_file_and_creates_pool(
        self,
        mock_upload_certificate_file,
        mock_save_or_update_certificate_pool,
    ):
        mock_upload_certificate_file.return_value = {
            "code": "0",
            "info": {"certificateUrl": "https://shein.example/uploaded/cert.pdf"},
        }
        mock_save_or_update_certificate_pool.return_value = {
            "code": "0",
            "info": {"certificatePoolId": 9001},
        }

        factory = SheinRemoteDocumentCreateFactory(
            sales_channel=self.sales_channel,
            media=self.media,
            media_through=self.media_through,
            remote_product=self.remote_product,
        )
        remote_document = factory.run()

        self.assertIsNotNone(remote_document)
        self.assertEqual(str(remote_document.remote_id), "9001")
        self.assertEqual(remote_document.remote_url, "https://shein.example/uploaded/cert.pdf")
        self.assertEqual(remote_document.remote_filename, "certificate.pdf")
        self.assertEqual(remote_document.remote_document_type_id, self.remote_document_type.id)

        mock_upload_certificate_file.assert_called_once()
        mock_save_or_update_certificate_pool.assert_called_once()

    def test_remote_document_create_raises_for_unsupported_extension(self):
        unsupported_media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=self.local_document_type,
        )
        unsupported_media.file.save("certificate.txt", ContentFile(b"plain"), save=True)

        factory = SheinRemoteDocumentCreateFactory(
            sales_channel=self.sales_channel,
            media=unsupported_media,
            remote_product=self.remote_product,
        )
        with self.assertRaises(PreFlightCheckError):
            factory.run()

    @patch.object(SheinRemoteDocumentCreateFactory, "_read_document_bytes")
    def test_remote_document_create_raises_when_file_exceeds_size_limit(self, mock_read_document_bytes):
        mock_read_document_bytes.return_value = b"a" * (SheinRemoteDocumentCreateFactory.MAX_FILE_SIZE_BYTES + 1)

        factory = SheinRemoteDocumentCreateFactory(
            sales_channel=self.sales_channel,
            media=self.media,
            remote_product=self.remote_product,
        )
        with self.assertRaises(PreFlightCheckError):
            factory.run()

    @patch.object(SheinDocumentThroughProductUpdateFactory, "save_certificate_pool_skc_bind")
    def test_document_assignment_update_binds_pool_and_sets_pending(self, mock_bind):
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_document_type=self.remote_document_type,
            remote_id="1001",
            remote_url="https://shein.example/uploaded/cert.pdf",
            remote_filename="certificate.pdf",
        )
        remote_association = baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            missing_status=SheinDocumentThroughProduct.STATUS_NEW,
        )

        factory = SheinDocumentThroughProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_instance=remote_association,
            remote_product=self.remote_product,
            skip_checks=True,
        )
        factory.run()

        remote_association.refresh_from_db()
        self.assertEqual(remote_association.missing_status, SheinDocumentThroughProduct.STATUS_PENDING)
        self.assertEqual(remote_association.remote_url, "https://shein.example/uploaded/cert.pdf")
        mock_bind.assert_called_once()

    @patch.object(SheinDocumentThroughProductUpdateFactory, "save_certificate_pool_skc_bind")
    def test_document_assignment_update_skips_bind_when_status_is_accepted(self, mock_bind):
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_document_type=self.remote_document_type,
            remote_id="1002",
            remote_url="https://shein.example/uploaded/cert.pdf",
            remote_filename="certificate.pdf",
        )
        remote_association = baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            missing_status=SheinDocumentThroughProduct.STATUS_ACCEPTED,
        )

        factory = SheinDocumentThroughProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_instance=remote_association,
            remote_product=self.remote_product,
            skip_checks=True,
        )
        factory.run()

        mock_bind.assert_not_called()

    @patch.object(SheinDocumentThroughProductUpdateFactory, "save_certificate_pool_skc_bind")
    def test_document_assignment_update_skips_bind_when_status_is_pending(self, mock_bind):
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_document_type=self.remote_document_type,
            remote_id="1003",
            remote_url="https://shein.example/uploaded/cert.pdf",
            remote_filename="certificate.pdf",
        )
        remote_association = baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
        )

        factory = SheinDocumentThroughProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_instance=remote_association,
            remote_product=self.remote_product,
            skip_checks=True,
        )
        factory.run()

        mock_bind.assert_not_called()

    @patch.object(SheinRemoteDocumentUpdateFactory, "run_create_factory")
    def test_remote_document_update_delegates_to_create_when_remote_url_missing(self, mock_run_create_factory):
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_document_type=self.remote_document_type,
            remote_id="2001",
            remote_url="",
        )
        mock_run_create_factory.return_value = remote_document

        factory = SheinRemoteDocumentUpdateFactory(
            sales_channel=self.sales_channel,
            media=self.media,
            remote_document=remote_document,
        )
        factory.run()

        mock_run_create_factory.assert_called_once()


class SheinProductFinalDocumentSyncTests(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.local_document_type_a = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="Document A",
        )
        self.local_document_type_b = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="Document B",
        )
        self.remote_document_type_a = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_document_type_a,
            remote_id="340",
            name="Type A",
            translated_name="Type A",
        )
        self.remote_document_type_b = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_document_type_b,
            remote_id="599",
            name="Type B",
            translated_name="Type B",
        )

    def _create_document_media_through(self, *, product, document_type, filename):
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=document_type,
        )
        media.file.save(filename, ContentFile(b"%PDF-1.4 data"), save=True)
        return MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            media=media,
            sales_channel=self.sales_channel,
        )

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_syncs_only_document_types_required_by_remote_rules(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SIMPLE-DOC-1",
        )
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
            remote_id="SPU-SIMPLE-1",
            spu_name="SPU-SIMPLE-1",
            skc_name="SKC-SIMPLE-1",
        )

        media_through_a = self._create_document_media_through(
            product=product,
            document_type=self.local_document_type_a,
            filename="a.pdf",
        )
        self._create_document_media_through(
            product=product,
            document_type=self.local_document_type_b,
            filename="b.pdf",
        )

        mock_get_certificate_rules.return_value = [
            {"certificateDimension": 1, "certificateTypeId": 340},
        ]
        mock_sync_document_assignment.side_effect = [
            SimpleNamespace(id=1),
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            skip_checks=True,
        )
        factory.final_process()

        self.assertEqual(mock_sync_document_assignment.call_count, 1)
        self.assertEqual(
            mock_sync_document_assignment.call_args.kwargs.get("media_through").id,
            media_through_a.id,
        )

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_raises_when_required_document_type_is_not_mapped(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SIMPLE-DOC-REQUIRED-NOT-MAPPED",
        )
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
            remote_id="SPU-SIMPLE-REQ-NOT-MAPPED",
            spu_name="SPU-SIMPLE-REQ-NOT-MAPPED",
            skc_name="SKC-SIMPLE-REQ-NOT-MAPPED",
        )

        self._create_document_media_through(
            product=product,
            document_type=self.local_document_type_a,
            filename="mapped-a.pdf",
        )
        baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=None,
            remote_id="111",
            name="Unmapped Required Type",
            translated_name="Unmapped Required Type Translated",
        )

        mock_get_certificate_rules.return_value = [
            {
                "certificateDimension": 1,
                "certificateTypeId": 111,
                "isRequired": True,
                "certificateTypeValue": "Rule Required Name",
            },
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            skip_checks=True,
        )

        with self.assertRaises(PreFlightCheckError) as raised:
            factory.final_process()

        self.assertIn(
            "Unmapped Required Type Translated (not mapped)",
            str(raised.exception),
        )
        mock_sync_document_assignment.assert_not_called()

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_raises_when_required_document_type_is_missing_on_product(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SIMPLE-DOC-REQUIRED-MISSING",
        )
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
            remote_id="SPU-SIMPLE-REQ-MISSING",
            spu_name="SPU-SIMPLE-REQ-MISSING",
            skc_name="SKC-SIMPLE-REQ-MISSING",
        )

        # Product includes only type A while required remote type below is mapped to local type B.
        self._create_document_media_through(
            product=product,
            document_type=self.local_document_type_a,
            filename="only-a.pdf",
        )

        mock_get_certificate_rules.return_value = [
            {
                "certificateDimension": 1,
                "certificateTypeId": 599,
                "isRequired": True,
                "certificateTypeValue": "Rule Type B",
            },
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            skip_checks=True,
        )

        with self.assertRaises(PreFlightCheckError) as raised:
            factory.final_process()

        self.assertIn("Type B (missing document)", str(raised.exception))
        mock_sync_document_assignment.assert_not_called()

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_sets_pending_external_documents_for_non_uploadable_required_types(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SIMPLE-DOC-EXTERNAL-1",
        )
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
            remote_id="SPU-SIMPLE-EXTERNAL-1",
            spu_name="SPU-SIMPLE-EXTERNAL-1",
            skc_name="SKC-SIMPLE-EXTERNAL-1",
            syncing_current_percentage=100,
            status=RemoteProduct.STATUS_PENDING_APPROVAL,
        )
        self._create_document_media_through(
            product=product,
            document_type=self.local_document_type_a,
            filename="external.pdf",
        )
        self.remote_document_type_a.uploadable = False
        self.remote_document_type_a.save(update_fields=["uploadable"])
        mock_get_certificate_rules.return_value = [
            {
                "certificateDimension": 1,
                "certificateTypeId": 340,
                "certificateTypeValue": "UK Agent",
                "isRequired": True,
                "certificateMissStatus": True,
            },
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            skip_checks=True,
        )
        factory.final_process()

        remote_product.refresh_from_db()
        self.assertEqual(
            remote_product.status,
            RemoteProduct.STATUS_PENDING_EXTERNAL_DOCUMENTS,
        )
        mock_sync_document_assignment.assert_not_called()

        log = RemoteLog.objects.filter(
            remote_product=remote_product,
            identifier=PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER,
            status=IntegrationLog.STATUS_SUCCESS,
            user_error=True,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("compliance manager", (log.response or "").lower())

    @patch.object(SheinProductExternalDocumentsFactory, "get_certificate_rule_by_product_spu")
    def test_external_documents_factory_resolves_back_to_pending_approval(
        self,
        mock_get_certificate_rules,
    ):
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SIMPLE-DOC-EXTERNAL-RESOLVED-1",
        )
        remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
            remote_id="SPU-SIMPLE-EXTERNAL-RESOLVED-1",
            spu_name="SPU-SIMPLE-EXTERNAL-RESOLVED-1",
            syncing_current_percentage=100,
            status=RemoteProduct.STATUS_PENDING_EXTERNAL_DOCUMENTS,
            pending_external_documents=True,
        )
        self.remote_document_type_a.uploadable = False
        self.remote_document_type_a.save(update_fields=["uploadable"])
        remote_product.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response="",
            payload={"spu_name": remote_product.spu_name},
            identifier=PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER,
            remote_product=remote_product,
            error_message="Waiting on SHEIN external documents.",
        )
        mock_get_certificate_rules.return_value = [
            {
                "certificateDimension": 1,
                "certificateTypeId": 340,
                "certificateTypeValue": "UK Agent",
                "isRequired": True,
                "certificateMissStatus": False,
            },
        ]

        factory = SheinProductExternalDocumentsFactory(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )
        self.assertFalse(factory.apply(log_missing=False))

        remote_product.refresh_from_db()
        self.assertEqual(remote_product.status, RemoteProduct.STATUS_PENDING_APPROVAL)
        self.assertTrue(
            RemoteLog.objects.filter(
                remote_product=remote_product,
                identifier=RESOLVED_EXTERNAL_DOCUMENTS_IDENTIFIER,
                status=IntegrationLog.STATUS_SUCCESS,
            ).exists()
        )

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_configurable_targets_each_variation_remote_product(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="CONF-PARENT-1",
        )
        variation_a = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONF-CHILD-A",
        )
        variation_b = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONF-CHILD-B",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation_a,
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation_b,
        )

        parent_remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
            remote_id="SPU-CONF-1",
            spu_name="SPU-CONF-1",
        )
        child_remote_product_a = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation_a,
            remote_parent_product=parent_remote_product,
            is_variation=True,
            remote_sku=variation_a.sku,
            remote_id="SKU-A",
            spu_name="SPU-CONF-1",
            skc_name="SKC-A",
        )
        child_remote_product_b = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation_b,
            remote_parent_product=parent_remote_product,
            is_variation=True,
            remote_sku=variation_b.sku,
            remote_id="SKU-B",
            spu_name="SPU-CONF-1",
            skc_name="SKC-B",
        )

        self._create_document_media_through(
            product=parent,
            document_type=self.local_document_type_a,
            filename="configurable.pdf",
        )

        mock_get_certificate_rules.return_value = [
            {"certificateDimension": 1, "certificateTypeId": 340},
        ]
        mock_sync_document_assignment.side_effect = [
            SimpleNamespace(id=11),
            SimpleNamespace(id=12),
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=parent_remote_product,
            skip_checks=True,
        )
        factory.final_process()

        called_remote_ids = {
            call.kwargs["remote_product"].id
            for call in mock_sync_document_assignment.call_args_list
        }
        self.assertEqual(called_remote_ids, {child_remote_product_a.id, child_remote_product_b.id})

    @patch.object(SheinProductCreateFactory, "_delete_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "_sync_document_assignment_for_remote_product")
    @patch.object(SheinProductCreateFactory, "get_certificate_rule_by_product_spu")
    def test_final_process_configurable_deduplicates_by_skc(
        self,
        mock_get_certificate_rules,
        mock_sync_document_assignment,
        _mock_delete_document_assignment,
    ):
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="CONF-PARENT-DEDUPE-SKC",
        )
        variation_a1 = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONF-CHILD-A1",
        )
        variation_a2 = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONF-CHILD-A2",
        )
        variation_b = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONF-CHILD-B1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation_a1,
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation_a2,
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation_b,
        )

        parent_remote_product = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
            remote_id="SPU-CONF-DEDUPE-SKC",
            spu_name="SPU-CONF-DEDUPE-SKC",
        )
        baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation_a1,
            remote_parent_product=parent_remote_product,
            is_variation=True,
            remote_sku=variation_a1.sku,
            remote_id="SKU-A1",
            spu_name="SPU-CONF-DEDUPE-SKC",
            skc_name="SKC-A",
        )
        baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation_a2,
            remote_parent_product=parent_remote_product,
            is_variation=True,
            remote_sku=variation_a2.sku,
            remote_id="SKU-A2",
            spu_name="SPU-CONF-DEDUPE-SKC",
            skc_name="SKC-A",
        )
        baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation_b,
            remote_parent_product=parent_remote_product,
            is_variation=True,
            remote_sku=variation_b.sku,
            remote_id="SKU-B1",
            spu_name="SPU-CONF-DEDUPE-SKC",
            skc_name="SKC-B",
        )

        self._create_document_media_through(
            product=parent,
            document_type=self.local_document_type_a,
            filename="configurable-dedupe-skc.pdf",
        )

        mock_get_certificate_rules.return_value = [
            {"certificateDimension": 1, "certificateTypeId": 340},
        ]
        mock_sync_document_assignment.side_effect = [
            SimpleNamespace(id=21),
            SimpleNamespace(id=22),
        ]

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=parent_remote_product,
            skip_checks=True,
        )
        factory.final_process()

        called_skc_names = {
            str(call.kwargs["remote_product"].skc_name)
            for call in mock_sync_document_assignment.call_args_list
        }
        self.assertEqual(mock_sync_document_assignment.call_count, 2)
        self.assertEqual(called_skc_names, {"SKC-A", "SKC-B"})
