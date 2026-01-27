from types import SimpleNamespace
from unittest.mock import patch

from model_bakery import baker

from core.tests import TransactionTestCase
from products.models import Product
from sales_channels.factories.task_queue import ProductPropertyAddTask, TaskTarget, GuardResult
from sales_channels.integrations.magento2.models import MagentoProduct, MagentoSalesChannel
from sales_channels import signals as sc_signals
from sales_channels.models import SyncRequest
from integrations.helpers import get_import_path


def _dummy_task():
    return None


def _dummy_product_task():
    return None


class DummyPropertyAddTask(ProductPropertyAddTask):
    sales_channel_class = MagentoSalesChannel
    live = False
    product_task_fallback = _dummy_product_task


class SyncRequestDedupeTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._connect_patcher = patch.object(
            MagentoSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

    def _make_remote_product(self, *, product, parent=None, is_variation=False):
        return MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_parent_product=parent,
            is_variation=is_variation,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _run_create_sync_request(self, *, task, remote_product, sync_type=None):
        guard_result = GuardResult(allowed=True, sync_type=sync_type)
        target = TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )
        task.create_sync_request(target=target, guard_result=guard_result)

    def test_property_twice_upgrades_to_product(self):
        parent_product = baker.make(Product, type='CONFIGURABLE', multi_tenant_company=self.multi_tenant_company, sku='PARENT')
        child_product = baker.make(Product, type="SIMPLE", multi_tenant_company=self.multi_tenant_company, sku='CHILD-1')
        parent_remote = self._make_remote_product(product=parent_product)
        child_remote = self._make_remote_product(product=child_product, parent=parent_remote, is_variation=True)

        task = DummyPropertyAddTask(
            task_func=_dummy_task,
            product=child_product,
        )
        task.set_extra_task_kwargs(local_instance_id=123)

        self._run_create_sync_request(task=task, remote_product=child_remote)
        self._run_create_sync_request(task=task, remote_product=child_remote)

        pending = SyncRequest.objects.filter(status=SyncRequest.STATUS_PENDING)
        skipped = SyncRequest.objects.filter(status=SyncRequest.STATUS_SKIPPED)

        self.assertEqual(pending.count(), 1)
        self.assertEqual(skipped.count(), 2)

        product_request = pending.first()
        self.assertEqual(product_request.sync_type, SyncRequest.TYPE_PRODUCT)
        self.assertEqual(product_request.task_func_path, get_import_path(_dummy_product_task))

        for skipped_request in skipped:
            self.assertEqual(skipped_request.skipped_for_id, product_request.id)

    def test_sibling_variations_escalate_to_parent(self):
        parent_product = baker.make(Product, type='CONFIGURABLE', multi_tenant_company=self.multi_tenant_company, sku='PARENT')
        child_product_1 = baker.make(Product, type="SIMPLE", multi_tenant_company=self.multi_tenant_company, sku='CHILD-1')
        child_product_2 = baker.make(Product, type="SIMPLE", multi_tenant_company=self.multi_tenant_company, sku='CHILD-2')
        parent_remote = self._make_remote_product(product=parent_product)
        child_remote_1 = self._make_remote_product(product=child_product_1, parent=parent_remote, is_variation=True)
        child_remote_2 = self._make_remote_product(product=child_product_2, parent=parent_remote, is_variation=True)

        task_1 = DummyPropertyAddTask(
            task_func=_dummy_task,
            product=child_product_1,
        )
        task_1.set_extra_task_kwargs(local_instance_id=111)

        task_2 = DummyPropertyAddTask(
            task_func=_dummy_task,
            product=child_product_2,
        )
        task_2.set_extra_task_kwargs(local_instance_id=222)

        self._run_create_sync_request(task=task_1, remote_product=child_remote_1)
        self._run_create_sync_request(task=task_1, remote_product=child_remote_1)
        self._run_create_sync_request(task=task_2, remote_product=child_remote_2)
        self._run_create_sync_request(task=task_2, remote_product=child_remote_2)

        pending = SyncRequest.objects.filter(status=SyncRequest.STATUS_PENDING)
        skipped = SyncRequest.objects.filter(status=SyncRequest.STATUS_SKIPPED)

        self.assertEqual(pending.count(), 1)
        self.assertEqual(skipped.count(), 6)

        product_request = pending.first()
        self.assertEqual(product_request.sync_type, SyncRequest.TYPE_PRODUCT)
        self.assertEqual(product_request.remote_product_id, parent_remote.id)

        for skipped_request in skipped:
            self.assertIsNotNone(skipped_request.skipped_for_id)
            if skipped_request.sync_type == SyncRequest.TYPE_PRODUCT:
                self.assertEqual(skipped_request.skipped_for_id, product_request.id)
            else:
                skipped_for = SyncRequest.objects.get(id=skipped_request.skipped_for_id)
                self.assertEqual(skipped_for.sync_type, SyncRequest.TYPE_PRODUCT)
