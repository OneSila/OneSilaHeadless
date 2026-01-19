from types import SimpleNamespace

from django.test import SimpleTestCase

from sales_channels.factories.task_queue import (
    AddTaskBase,
    AddTaskConfigError,
    ChannelScopedAddTask,
    DeleteScopedAddTask,
    MarketplaceAddTask,
    ProductDeleteScopedAddTask,
    ViewScopedAddTask,
)


class TaskQueueConfigTests(SimpleTestCase):
    def test_base_class_cannot_be_used_directly(self, *, _unused=None):
        with self.assertRaises(AddTaskConfigError):
            AddTaskBase(task_func=lambda: None, multi_tenant_company=object())

    def test_missing_task_func_raises(self, *, _unused=None):
        class DummyAddTask(AddTaskBase):
            pass

        with self.assertRaises(AddTaskConfigError):
            DummyAddTask(task_func=None, multi_tenant_company=object())

    def test_missing_sales_channel_class_raises(self, *, _unused=None):
        with self.assertRaises(AddTaskConfigError):
            ChannelScopedAddTask(
                task_func=lambda: None,
                multi_tenant_company=object(),
            )

    def test_missing_sync_type_when_not_live_raises(self, *, _unused=None):
        class DummyMarketplaceTask(MarketplaceAddTask):
            pass

        with self.assertRaises(AddTaskConfigError):
            DummyMarketplaceTask(task_func=lambda: None, multi_tenant_company=object())

    def test_missing_remote_class_raises(self, *, _unused=None):
        class DummyDeleteTask(DeleteScopedAddTask):
            sales_channel_class = object

        with self.assertRaises(AddTaskConfigError):
            DummyDeleteTask(
                task_func=lambda: None,
                multi_tenant_company=object(),
                local_instance_id=1,
            )

    def test_missing_view_assign_model_raises(self, *, _unused=None):
        class DummyViewTask(ViewScopedAddTask):
            sales_channel_class = object

        product = SimpleNamespace(multi_tenant_company=object())
        with self.assertRaises(AddTaskConfigError):
            DummyViewTask(
                task_func=lambda: None,
                product=product,
            )

    def test_product_delete_requires_product(self, *, _unused=None):
        class DummyProductDeleteTask(ProductDeleteScopedAddTask):
            sales_channel_class = object
            remote_class = object

        with self.assertRaises(TypeError):
            DummyProductDeleteTask(
                task_func=lambda: None,
                multi_tenant_company=object(),
                local_instance_id=1,
            )

    def test_valid_config_passes(self, *, _unused=None):
        class DummyTask(ChannelScopedAddTask):
            sales_channel_class = object

        instance = DummyTask(
            task_func=lambda: None,
            multi_tenant_company=object(),
        )
        self.assertIsNotNone(instance)
