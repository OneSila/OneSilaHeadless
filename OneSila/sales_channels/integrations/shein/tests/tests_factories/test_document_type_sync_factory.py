"""Tests for syncing Shein certificate rules into remote document types."""

from __future__ import annotations

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.factories.sales_channels.document_types import (
    SheinCertificateRuleSyncFactory,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinDocumentType,
    SheinSalesChannel,
)


class _JsonResponse:
    def __init__(self, *, payload):
        self._payload = payload

    def json(self):
        return self._payload


class SheinCertificateRuleSyncFactoryTest(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            hostname="https://shein-docs-sync.example.com",
            open_key_id="open-key",
            secret_key="secret-key",
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="1001",
            name="Category 1001",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="1002",
            name="Category 1002",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_run_creates_document_types_and_ignores_store_level_entries(self):
        factory = SheinCertificateRuleSyncFactory(
            sales_channel=self.sales_channel,
            category_remote_id="1001",
            uploadable_certificate_type_ids={"2001"},
        )
        response = _JsonResponse(
            payload={
                "info": {
                    "data": [
                        {
                            "certificateDimension": 1,
                            "certificateTypeId": 2001,
                            "certificateTypeValue": "CPC",
                            "isRequired": True,
                        },
                        {
                            "certificateDimension": 2,
                            "certificateTypeId": 2002,
                            "certificateTypeValue": "Store Level",
                            "isRequired": False,
                        },
                    ]
                }
            }
        )

        with patch.object(
            SheinCertificateRuleSyncFactory,
            "shein_post",
            return_value=response,
        ) as mock_post:
            stats = factory.run()

        mock_post.assert_called_once_with(
            path="/open-api/goods/get-certificate-rule",
            payload={"categoryId": 1001, "systemId": "spmp"},
        )
        self.assertEqual(stats["categories_processed"], 1)
        self.assertEqual(stats["rules_processed"], 1)
        self.assertEqual(stats["document_types_created"], 1)

        document_type = SheinDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="2001",
        )
        self.assertEqual(document_type.name, "CPC")
        self.assertTrue(document_type.uploadable)
        self.assertEqual(document_type.required_categories, ["1001"])
        self.assertEqual(document_type.optional_categories, [])
        self.assertFalse(
            SheinDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id="2002",
            ).exists()
        )

    def test_run_moves_category_between_required_and_optional(self):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="3001",
            name="Before",
            required_categories=["1001"],
            optional_categories=[],
        )
        factory = SheinCertificateRuleSyncFactory(
            sales_channel=self.sales_channel,
            category_remote_id="1001",
            uploadable_certificate_type_ids=set(),
        )
        response = _JsonResponse(
            payload={
                "info": {
                    "data": [
                        {
                            "certificateDimension": 1,
                            "certificateTypeId": 3001,
                            "certificateTypeValue": "After",
                            "isRequired": False,
                        }
                    ]
                }
            }
        )

        with patch.object(
            SheinCertificateRuleSyncFactory,
            "shein_post",
            return_value=response,
        ):
            stats = factory.run()

        document_type.refresh_from_db()
        self.assertEqual(stats["document_types_created"], 0)
        self.assertEqual(stats["document_types_updated"], 1)
        self.assertEqual(document_type.name, "After")
        self.assertFalse(document_type.uploadable)
        self.assertEqual(document_type.required_categories, [])
        self.assertEqual(document_type.optional_categories, ["1001"])

    def test_uploadable_field_is_persisted_on_document_type(self):
        uploadable_document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="4001",
            name="Uploadable",
            uploadable=True,
        )
        external_document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="4002",
            name="External Only",
            uploadable=False,
        )

        self.assertTrue(uploadable_document_type.uploadable)
        self.assertFalse(external_document_type.uploadable)
