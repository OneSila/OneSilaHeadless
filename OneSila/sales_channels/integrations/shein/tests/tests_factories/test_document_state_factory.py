from unittest.mock import PropertyMock, patch

from model_bakery import baker

from core.tests import TestCase
from integrations.models import IntegrationLog
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableVariation, Product
from sales_channels.integrations.shein.factories.products.document_state import (
    SheinProductDocumentStateFactory,
)
from sales_channels.integrations.shein.factories.imports.product_refresh import (
    SheinProductDetailRefreshFactory,
)
from sales_channels.integrations.shein.models import (
    SheinDocument,
    SheinDocumentThroughProduct,
    SheinDocumentType,
    SheinProduct,
    SheinProductIssue,
    SheinSalesChannel,
)
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


class SheinDocumentStateFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku=self.product.sku,
            spu_name="SPU-1",
            syncing_current_percentage=100,
        )

    @patch.object(SheinProductDocumentStateFactory, "get_certificate_rule_by_product_spu")
    @patch("sales_channels.models.products.RemoteProduct.errors", new_callable=PropertyMock)
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_review_failures_mark_approval_rejected(self, fetch_mock, errors_mock, get_certificate_rules_mock) -> None:
        errors_mock.return_value = IntegrationLog.objects.none()
        get_certificate_rules_mock.return_value = []
        fetch_mock.return_value = {
            "info": {
                "data": [
                    {
                        "spuName": "SPU-1",
                        "version": "V1",
                        "skcList": [
                            {
                                "skcName": "SKC-1",
                                "documentState": 3,
                                "documentSn": "DOC-1",
                                "failedReason": ["Brand issue"],
                            }
                        ],
                    }
                ]
            }
        }

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        factory.run()

        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_APPROVAL_REJECTED)

        log = RemoteLog.objects.filter(
            remote_product=self.remote_product,
            identifier="SheinProductDocumentState:review_failed",
            user_error=True,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("brand issue", (log.response or "").lower())

    @patch.object(SheinProductDocumentStateFactory, "get_certificate_rule_by_product_spu")
    @patch.object(SheinProductDetailRefreshFactory, "run")
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_approval_completion_refreshes_details(self, fetch_mock, refresh_mock, get_certificate_rules_mock) -> None:
        get_certificate_rules_mock.return_value = []
        fetch_mock.return_value = {
            "info": {
                "data": [
                    {
                        "spuName": "SPU-1",
                        "version": "V2",
                        "skcList": [
                            {
                                "skcName": "SKC-1",
                                "documentState": 2,
                                "documentSn": "DOC-2",
                                "failedReason": [],
                            }
                        ],
                    }
                ]
            }
        }
        self.remote_product.status = RemoteProduct.STATUS_PENDING_APPROVAL
        self.remote_product.save(update_fields=["status"])

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        factory.run()

        refresh_mock.assert_called_once()

    @patch.object(SheinProductDocumentStateFactory, "get_certificate_rule_by_product_spu")
    @patch.object(SheinProductDetailRefreshFactory, "run")
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_completion_stays_pending_when_variation_document_is_pending(
        self,
        fetch_mock,
        refresh_mock,
        get_certificate_rules_mock,
    ) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="PARENT-SKU-1",
        )
        variation = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="VAR-SKU-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation,
        )

        parent_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
            remote_id="SPU-PARENT-1",
            spu_name="SPU-PARENT-1",
            syncing_current_percentage=100,
            status=RemoteProduct.STATUS_PENDING_APPROVAL,
        )
        variation_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation,
            remote_parent_product=parent_remote,
            is_variation=True,
            remote_sku=variation.sku,
            remote_id="SKU-VAR-1",
            spu_name="SPU-PARENT-1",
            skc_name="SKC-1",
            syncing_current_percentage=100,
            status=RemoteProduct.STATUS_PENDING_APPROVAL,
        )

        local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="UK Agent",
        )
        remote_document_type = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id="340",
            name="UK Agent",
            translated_name="UK Agent",
        )
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=local_document_type,
        )
        media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=variation,
            media=media,
        )
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media,
            remote_document_type=remote_document_type,
            remote_id="POOL-1",
        )
        baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=variation_remote,
            remote_document=remote_document,
            missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
        )

        fetch_mock.return_value = {
            "info": {
                "data": [
                    {
                        "spuName": "SPU-PARENT-1",
                        "version": "V2",
                        "skcList": [
                            {
                                "skcName": "SKC-1",
                                "documentState": 2,
                                "documentSn": "DOC-2",
                                "failedReason": [],
                            }
                        ],
                    }
                ]
            }
        }
        get_certificate_rules_mock.return_value = [
            {
                "certificateTypeId": 340,
                "certificateDimension": 1,
                "certificateMissStatus": True,
            }
        ]

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=parent_remote,
        )
        factory.run()

        parent_remote.refresh_from_db()
        self.assertEqual(parent_remote.status, RemoteProduct.STATUS_PENDING_APPROVAL)
        refresh_mock.assert_not_called()

    @patch.object(SheinProductDocumentStateFactory, "get_certificate_rule_by_product_spu")
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_certificate_rules_sync_marks_pending_association_as_accepted(
        self,
        fetch_mock,
        get_certificate_rules_mock,
    ) -> None:
        local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="UK Agent",
        )
        remote_document_type = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id="340",
            name="UK Agent",
            translated_name="UK Agent",
        )
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=local_document_type,
        )
        media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            media=media,
        )
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media,
            remote_document_type=remote_document_type,
            remote_id="POOL-100",
        )
        association = baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            remote_id="PQMS-100",
            missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
        )

        fetch_mock.return_value = {"info": {"data": []}}
        get_certificate_rules_mock.return_value = [
            {
                "certificateTypeId": 340,
                "certificateDimension": 1,
                "certificateMissStatus": False,
                "certificatePoolList": [
                    {
                        "certificatePoolId": "POOL-100",
                        "pqmsCertificateSn": "PQMS-100",
                        "auditStatus": "1",
                    }
                ],
            }
        ]

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        factory.run()

        association.refresh_from_db()
        self.assertEqual(association.missing_status, SheinDocumentThroughProduct.STATUS_ACCEPTED)

    @patch.object(SheinProductDocumentStateFactory, "get_certificate_rule_by_product_spu")
    @patch.object(SheinProductDocumentStateFactory, "fetch")
    def test_certificate_rules_sync_accepts_by_remote_url_match(
        self,
        fetch_mock,
        get_certificate_rules_mock,
    ) -> None:
        local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="UK Agent URL Match",
        )
        remote_document_type = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id="340",
            name="UK Agent URL Match",
            translated_name="UK Agent URL Match",
        )
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=local_document_type,
        )
        media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            media=media,
        )
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media,
            remote_document_type=remote_document_type,
            remote_id="POOL-URL-100",
            remote_url="https://files.example.com/url-match-cert.pdf",
        )
        association = baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            remote_id="PQMS-URL-100",
            remote_url="https://files.example.com/url-match-cert.pdf",
            missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
        )

        fetch_mock.return_value = {"info": {"data": []}}
        get_certificate_rules_mock.return_value = [
            {
                "certificateTypeId": 340,
                "certificateDimension": 1,
                "certificateMissStatus": False,
                "certificatePoolList": [
                    {
                        # Deliberately different IDs to prove URL-driven acceptance.
                        "certificatePoolId": "POOL-OTHER",
                        "pqmsCertificateSn": "PQMS-OTHER",
                        "auditStatus": "1",
                        "certificatePoolFileList": [
                            {
                                "certificateUrlName": "url-match-cert.pdf",
                                "certificateUrl": "https://files.example.com/url-match-cert.pdf",
                            }
                        ],
                    }
                ],
            }
        ]

        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        factory.run()

        association.refresh_from_db()
        self.assertEqual(association.missing_status, SheinDocumentThroughProduct.STATUS_ACCEPTED)

    def test_determine_status_keeps_pending_when_issue_completed_but_variation_document_pending(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="PARENT-DET-1",
        )
        variation = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="VAR-DET-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation,
        )

        parent_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
            remote_id="SPU-DET-1",
            spu_name="SPU-DET-1",
            syncing_current_percentage=100,
        )
        variation_remote = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=variation,
            remote_parent_product=parent_remote,
            is_variation=True,
            remote_sku=variation.sku,
            remote_id="SKU-DET-1",
            spu_name="SPU-DET-1",
            skc_name="SKC-DET-1",
            syncing_current_percentage=100,
        )

        local_document_type = baker.make(
            DocumentType,
            multi_tenant_company=self.multi_tenant_company,
            name="UK Agent",
        )
        remote_document_type = baker.make(
            SheinDocumentType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id="340",
            name="UK Agent",
            translated_name="UK Agent",
        )
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=local_document_type,
        )
        media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=variation,
            media=media,
        )
        remote_document = baker.make(
            SheinDocument,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media,
            remote_document_type=remote_document_type,
            remote_id="POOL-DET-1",
        )
        baker.make(
            SheinDocumentThroughProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=variation_remote,
            remote_document=remote_document,
            missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
        )
        SheinProductIssue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_product=parent_remote,
            version="V1",
            document_sn="DOC-DET-1",
            skc_name="SKC-DET-1",
            document_state=2,
            failed_reason=[],
            is_active=False,
        )

        self.assertEqual(parent_remote._determine_status(), RemoteProduct.STATUS_PENDING_APPROVAL)
