from unittest.mock import patch

from django.db import transaction

from core.tests import TestCase
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from products.models import Product
from sales_channels.integrations.shein.models import (
    SheinDocumentType,
    SheinProduct,
    SheinSalesChannel,
)
from sales_channels.integrations.shein.tasks import resync_shein_product_db_task
from sales_channels.signals import manual_sync_remote_product


class SheinLiveReceiversTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = SheinProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def test_shein_manual_sync_queues_task(self, *, _unused=None):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            manual_sync_remote_product.send(
                sender=SheinProduct,
                instance=self.remote_product,
            )

        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 1,
        )
        task = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).latest("id")
        self.assertEqual(task.task_name, get_import_path(resync_shein_product_db_task))
        self.assertEqual(task.task_kwargs.get("sales_channel_id"), self.sales_channel.id)
        self.assertEqual(task.task_kwargs.get("product_id"), self.product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), self.remote_product.id)

    @patch("sales_channels.integrations.shein.receivers.shein_translate_document_type_task")
    def test_shein_document_type_create_triggers_translation_when_missing(self, task_mock):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT-1",
            name="能效标识certificate_type_id4",
        )

        task_mock.assert_called_once_with(document_type_id=document_type.id)

    @patch("sales_channels.integrations.shein.receivers.shein_translate_document_type_task")
    def test_shein_document_type_create_skips_translation_when_already_translated(self, task_mock):
        SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT-2",
            name="Certificate",
            translated_name="Certificate",
        )

        task_mock.assert_not_called()

    @patch("sales_channels.integrations.shein.receivers.shein_translate_document_type_task")
    def test_shein_document_type_update_triggers_translation_when_translated_name_empty(self, task_mock):
        document_type = SheinDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERT-3",
            name="证书类型",
            translated_name="",
        )
        task_mock.reset_mock()

        document_type.name = "新证书类型"
        document_type.save(update_fields=["name"])

        task_mock.assert_called_once_with(document_type_id=document_type.id)
