"""Tests for Shein integration Huey tasks."""

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.models import (
    SheinDocumentType,
    SheinProduct,
    SheinSalesChannel,
)
from sales_channels.integrations.shein.tasks import (
    delete_shein_product_db_task,
    shein__tasks__refresh_product_issues__cronjob,
    shein_import_db_task,
    shein_translate_document_type_task,
)
from sales_channels.models import SalesChannelImport


class SheinImportTasksTest(TestCase):
    """Validate the orchestration performed by the Shein Huey tasks."""

    def setUp(self):
        super().setUp()
        self.sales_channel: SheinSalesChannel = baker.make(
            SheinSalesChannel,
            hostname="https://tasks.shein.example.com",
            secret_key="secret",
            open_key_id="open",
        )
        self.import_process = baker.make(
            SalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

    def test_shein_import_db_task_runs_processor(self):
        with patch(
            "sales_channels.integrations.shein.tasks.SheinSchemaImportProcessor"
        ) as mock_processor:
            shein_import_db_task(
                import_process=self.import_process,
                sales_channel=self.sales_channel,
            )

        mock_processor.assert_called_once_with(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        mock_processor.return_value.run.assert_called_once_with()

    def test_shein_translate_document_type_task_runs_factory(self):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT-3",
            name="证书类型",
        )

        with patch(
            "sales_channels.integrations.shein.factories.sales_channels.SheinDocumentTypeTranslationFactory"
        ) as mock_factory:
            shein_translate_document_type_task(document_type_id=document_type.id)

        mock_factory.assert_called_once()
        called_document_type = mock_factory.call_args.kwargs.get("document_type")
        self.assertEqual(called_document_type.id, document_type.id)
        mock_factory.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.shein.tasks.BaseRemoteTask")
    @patch("sales_channels.integrations.shein.factories.products.SheinProductDeleteFactory")
    def test_delete_shein_product_db_task_runs_factory(
        self,
        mock_delete_factory,
        mock_base_task,
    ):
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=baker.make("products.Product", multi_tenant_company=self.multi_tenant_company, type='SIMPLE'),
            remote_id="SPU-123",
        )

        task_instance = mock_base_task.return_value

        def execute_side_effect(callable_obj):
            callable_obj()

        task_instance.execute.side_effect = execute_side_effect

        delete_shein_product_db_task.call_local(
            1,
            sales_channel_id=self.sales_channel.id,
            remote_instance=remote_product.id,
        )

        mock_base_task.assert_called_once_with(1)
        mock_delete_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            remote_instance=remote_product.id,
        )
        mock_delete_factory.return_value.run.assert_called_once_with()
