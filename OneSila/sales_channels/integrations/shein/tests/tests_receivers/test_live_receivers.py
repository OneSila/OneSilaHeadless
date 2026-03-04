from unittest.mock import patch

from django.db import transaction

from core.tests import TestCase
from integrations.helpers import get_import_path
from products.models import Product
from sales_channels.integrations.shein.models import (
    SheinDocumentType,
    SheinProduct,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.tasks import (
    delete_shein_product_db_task,
    resync_shein_product_db_task,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.signals import delete_remote_product, manual_sync_remote_product


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
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Default",
            url="https://example.shein.local",
            is_default=True,
        )

    def test_shein_manual_sync_queues_task(self, *, _unused=None):
        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            manual_sync_remote_product.send(
                sender=SheinProduct,
                instance=self.remote_product,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(resync_shein_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "product_id": self.product.id,
                "remote_product_id": self.remote_product.id,
            },
            number_of_remote_requests=1,
        )

    def test_shein_product_delete_from_assign_queues_task(self, *, _unused=None):
        assign = SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )
        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product.send(
                sender=SalesChannelViewAssign,
                instance=assign,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(delete_shein_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "remote_instance": self.remote_product.id,
            },
            number_of_remote_requests=None,
        )

    def test_shein_product_delete_from_product_queues_task(self, *, _unused=None):
        with patch(
            "sales_channels.factories.task_queue.task_queue.add_task_to_queue",
        ) as add_task_mock, patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product.send(
                sender=self.product.__class__,
                instance=self.product,
            )

        add_task_mock.assert_called_once_with(
            integration_id=self.sales_channel.id,
            task_func_path=get_import_path(delete_shein_product_db_task),
            task_kwargs={
                "sales_channel_id": self.sales_channel.id,
                "remote_instance": self.remote_product.id,
            },
            number_of_remote_requests=None,
        )

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
