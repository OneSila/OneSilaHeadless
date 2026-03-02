from unittest.mock import patch

from core.tests import TestCase
from sales_channels.integrations.shein.factories.sales_channels import (
    SheinDocumentTypeTranslationFactory,
)
from sales_channels.integrations.shein.models import SheinDocumentType, SheinSalesChannel


class SheinDocumentTypeTranslationFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein-doc-translate.test",
            remote_id="SHEIN-TR",
        )

    def test_run_translates_cjk_name_and_cleans_certificate_type_suffix(self):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="4",
            name="能效标识certificate_type_id4",
        )

        with patch(
            "sales_channels.integrations.shein.factories.sales_channels.document_type_translations.TranslateRemotePropertyFlow.flow",
            return_value="Energy Label certificate_type_id4",
        ) as mock_translate:
            translated_name = SheinDocumentTypeTranslationFactory(
                document_type=document_type
            ).run()

        document_type.refresh_from_db()
        self.assertEqual(translated_name, "Energy Label")
        self.assertEqual(document_type.translated_name, "Energy Label")
        mock_translate.assert_called_once_with()

    def test_run_cleans_non_cjk_name_without_llm(self):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="5",
            name="Safety Label certificate_type_id5",
        )

        with patch(
            "sales_channels.integrations.shein.factories.sales_channels.document_type_translations.TranslateRemotePropertyFlow.flow"
        ) as mock_translate:
            translated_name = SheinDocumentTypeTranslationFactory(
                document_type=document_type
            ).run()

        document_type.refresh_from_db()
        self.assertEqual(translated_name, "Safety Label")
        self.assertEqual(document_type.translated_name, "Safety Label")
        mock_translate.assert_not_called()
