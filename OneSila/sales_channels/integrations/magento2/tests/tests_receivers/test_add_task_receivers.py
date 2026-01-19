from unittest.mock import patch

from core.tests import TransactionTestCase
from django.db import transaction
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from properties.signals import product_properties_rule_created
from products.models import Product
from sales_channels.signals import sales_view_assign_updated
from sales_channels.tests.helpers import TaskQueueDispatchPatchMixin

from sales_channels.integrations.magento2.tests.mixins import MagentoSalesChannelTestMixin
from sales_channels.integrations.magento2.tasks import (
    create_magento_attribute_set_task,
    update_magento_sales_view_assign_db_task,
)


class MagentoAddToTaskReceiverTests(
    TaskQueueDispatchPatchMixin,
    MagentoSalesChannelTestMixin,
    TransactionTestCase,
):
    def test_assign_update_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-ASSIGN-1",
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            sales_view_assign_updated.send(
                sender=product.__class__,
                instance=product,
                sales_channel=self.sales_channel,
                view=None,
            )

        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 1,
        )

        task = IntegrationTaskQueue.objects.get(integration_id=self.sales_channel.id)
        self.assertEqual(
            task.task_name,
            get_import_path(update_magento_sales_view_assign_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)

    def test_attribute_set_create_queues_task(self, *, _unused=None):
        property_instance = Property.objects.get(
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_value = PropertySelectValue.objects.create(
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        )
        rule = ProductPropertiesRule.objects.get(
            product_type=select_value,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel__isnull=True,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            product_properties_rule_created.send(
                sender=rule.__class__,
                instance=rule,
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
        self.assertEqual(
            task.task_name,
            get_import_path(create_magento_attribute_set_task),
        )
        self.assertEqual(task.task_kwargs.get("rule_id"), rule.id)
