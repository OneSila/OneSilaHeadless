from unittest.mock import patch

from core.tests import TransactionTestCase
from django.db import transaction
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from currencies.models import Currency
from media.models import Media, MediaProductThrough
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from properties.models import ProductProperty
from properties.signals import (
    product_properties_rule_created,
    product_properties_rule_rename,
    product_properties_rule_updated,
)
from products.models import ConfigurableVariation, Product
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_product,
    create_remote_vat_rate,
    create_remote_image_association,
    delete_remote_product,
    delete_remote_property,
    delete_remote_property_select_value,
    delete_remote_image,
    remove_remote_product_variation,
    sales_view_assign_updated,
    sync_remote_product,
    update_remote_image_association,
    delete_remote_image_association,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_eancode,
    create_remote_product_property,
    update_remote_product_property,
    delete_remote_product_property,
    update_remote_property,
    update_remote_property_select_value,
    update_remote_vat_rate,
)
from sales_channels.tests.helpers import TaskQueueDispatchPatchMixin
from taxes.models import VatRate

from sales_channels.integrations.magento2.tests.mixins import MagentoSalesChannelTestMixin
from sales_channels.integrations.magento2.tasks import (
    add_magento_product_variation_db_task,
    create_magento_attribute_set_task,
    create_magento_image_association_db_task,
    create_magento_product_db_task,
    create_magento_vat_rate_db_task,
    delete_magento_attribute_set_task,
    delete_magento_image_db_task,
    delete_magento_image_association_db_task,
    delete_magento_product_db_task,
    delete_magento_property_db_task,
    delete_magento_property_select_value_task,
    delete_magento_product_property_db_task,
    remove_magento_product_variation_db_task,
    update_magento_attribute_set_task,
    update_magento_image_association_db_task,
    update_magento_price_db_task,
    update_magento_product_content_db_task,
    update_magento_product_db_task,
    update_magento_product_eancode_db_task,
    update_magento_product_property_db_task,
    update_magento_property_db_task,
    update_magento_property_select_value_task,
    update_magento_sales_view_assign_db_task,
    update_magento_vat_rate_db_task,
    sync_magento_product_db_task,
    create_magento_product_property_db_task,
)
from sales_channels.integrations.magento2.models.products import MagentoImageProductAssociation
from sales_channels.integrations.magento2.models.properties import (
    MagentoAttributeSet,
    MagentoProductProperty,
    MagentoProperty,
    MagentoPropertySelectValue,
)
from sales_channels.integrations.magento2.models.products import MagentoProduct
from sales_channels.integrations.magento2.models.sales_channels import MagentoSalesChannelView


class MagentoAddToTaskReceiverTests(
    TaskQueueDispatchPatchMixin,
    MagentoSalesChannelTestMixin,
    TransactionTestCase,
):
    def setUp(self, *, _unused=None):
        super().setUp()
        self.product_type_property = Property.objects.get(
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )

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
        select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
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

    def test_attribute_set_delete_queues_task(self, *, _unused=None):
        select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        rule = ProductPropertiesRule.objects.get(
            product_type=select_value,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel__isnull=True,
        )
        attribute_set = MagentoAttributeSet.objects.create(
            local_instance=rule,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            rule.delete()

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
            get_import_path(delete_magento_attribute_set_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), attribute_set.id)

    def test_attribute_set_rename_queues_task(self, *, _unused=None):
        select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
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
            product_properties_rule_rename.send(
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
            get_import_path(update_magento_attribute_set_task),
        )
        self.assertEqual(task.task_kwargs.get("rule_id"), rule.id)
        self.assertTrue(task.task_kwargs.get("update_name_only"))

    def test_attribute_set_update_queues_task(self, *, _unused=None):
        select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
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
            product_properties_rule_updated.send(
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
            get_import_path(update_magento_attribute_set_task),
        )
        self.assertEqual(task.task_kwargs.get("rule_id"), rule.id)

    def test_image_delete_queues_task(self, *, _unused=None):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_image.send(
                sender=image.__class__,
                instance=image,
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
            get_import_path(delete_magento_image_db_task),
        )
        self.assertEqual(task.task_kwargs.get("image_id"), image.id)

    def test_property_update_queues_task(self, *, _unused=None):
        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_property.send(
                sender=self.product_type_property.__class__,
                instance=self.product_type_property,
                language="en",
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
            get_import_path(update_magento_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("property_id"), self.product_type_property.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_property_select_value_update_queues_task(self, *, _unused=None):
        select_value = PropertySelectValue.objects.create(
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_property_select_value.send(
                sender=select_value.__class__,
                instance=select_value,
                language="en",
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
            get_import_path(update_magento_property_select_value_task),
        )
        self.assertEqual(task.task_kwargs.get("property_select_value_id"), select_value.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_product_variation_add_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-PARENT-1",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-VAR-1",
            type=Product.SIMPLE,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            add_remote_product_variation.send(
                sender=ConfigurableVariation,
                parent_product=parent_product,
                variation_product=variation_product,
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
            get_import_path(add_magento_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_product_variation_remove_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-PARENT-2",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-VAR-2",
            type=Product.SIMPLE,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            remove_remote_product_variation.send(
                sender=ConfigurableVariation,
                parent_product=parent_product,
                variation_product=variation_product,
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
            get_import_path(remove_magento_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_product_create_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="MAG-CREATE-1",
            type=Product.SIMPLE,
        )
        view = MagentoSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            code="default",
            name="Default",
            multi_tenant_company=self.multi_tenant_company,
        )
        assign = SalesChannelViewAssign.objects.create(
            product=product,
            sales_channel_view=view,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_product.send(
                sender=assign.__class__,
                instance=assign,
                view=view
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
            get_import_path(create_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)

    def test_vat_rate_create_queues_task(self, *, _unused=None):
        vat_rate = VatRate.objects.create(
            name="VAT 21",
            rate=21,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_vat_rate.send(
                sender=vat_rate.__class__,
                instance=vat_rate,
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
            get_import_path(create_magento_vat_rate_db_task),
        )
        self.assertEqual(task.task_kwargs.get("vat_rate_id"), vat_rate.id)

    def test_vat_rate_update_queues_task(self, *, _unused=None):
        vat_rate = VatRate.objects.create(
            name="VAT 10",
            rate=10,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_vat_rate.send(
                sender=vat_rate.__class__,
                instance=vat_rate,
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
            get_import_path(update_magento_vat_rate_db_task),
        )
        self.assertEqual(task.task_kwargs.get("vat_rate_id"), vat_rate.id)


class MagentoProductScopedAddReceiverTests(
    TaskQueueDispatchPatchMixin,
    MagentoSalesChannelTestMixin,
    TransactionTestCase,
):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._populate_title_patcher = patch(
            "media.tasks.populate_media_title_task",
            return_value=None,
        )
        self._populate_title_patcher.start()
        self.addCleanup(self._populate_title_patcher.stop)

    def _create_product_and_remote(self, *, sku):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
            type=Product.SIMPLE,
        )
        remote_product = MagentoProduct.objects.create(
            local_instance=product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        return product, remote_product

    def test_media_product_through_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-IMG-1")
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=product,
            media=image,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_image_association.send(
                sender=media_product_through.__class__,
                instance=media_product_through,
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
            get_import_path(create_magento_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(
            task.task_kwargs.get("remote_product_id"),
            remote_product.id,
        )

    def test_media_product_through_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-IMG-2")
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=product,
            media=image,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_image_association.send(
                sender=media_product_through.__class__,
                instance=media_product_through,
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
            get_import_path(update_magento_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(
            task.task_kwargs.get("remote_product_id"),
            remote_product.id,
        )

    def test_media_product_through_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-IMG-3")
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=product,
            media=image,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_association = MagentoImageProductAssociation.objects.create(
            local_instance=media_product_through,
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_image_association.send(
                sender=media_product_through.__class__,
                instance=media_product_through,
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
            get_import_path(delete_magento_image_association_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_association.id)

    def test_price_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-PRICE-1")
        currency = Currency.objects.create(
            iso_code="USD",
            name="US Dollar",
            symbol="$",
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_price.send(
                sender=product.__class__,
                instance=product,
                currency=currency,
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
            get_import_path(update_magento_price_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("currency_id"), currency.id)

    def test_product_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-UPD-1")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_product.send(
                sender=product.__class__,
                instance=product,
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
            get_import_path(update_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_product_content_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-CONT-1")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_product_content.send(
                sender=product.__class__,
                instance=product,
                language="en",
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
            get_import_path(update_magento_product_content_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_product_eancode_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-EAN-1")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_product_eancode.send(
                sender=product.__class__,
                instance=product,
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
            get_import_path(update_magento_product_eancode_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_product_property_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-PROP-1")
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=property_instance,
            value_int=5,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_product_property.send(
                sender=product_property.__class__,
                instance=product_property,
                language="en",
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
            get_import_path(create_magento_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_product_property_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-PROP-2")
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=property_instance,
            value_int=7,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            update_remote_product_property.send(
                sender=product_property.__class__,
                instance=product_property,
                language="en",
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
            get_import_path(update_magento_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_product_property_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-PROP-3")
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=property_instance,
            value_int=9,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_property = MagentoProductProperty.objects.create(
            local_instance=product_property,
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product_property.send(
                sender=product_property.__class__,
                instance=product_property,
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
            get_import_path(delete_magento_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_property.id)

    def test_product_sync_from_product_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-SYNC-1")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            sync_remote_product.send(
                sender=product.__class__,
                instance=product,
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
            get_import_path(sync_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_product_sync_from_remote_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-SYNC-2")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            sync_remote_product.send(
                sender=remote_product.__class__,
                instance=remote_product,
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
            get_import_path(sync_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_product_delete_from_assign_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-DEL-ASSIGN-1")
        view = MagentoSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            code="delete-assign",
            name="Delete Assign",
            multi_tenant_company=self.multi_tenant_company,
        )
        assign = SalesChannelViewAssign.objects.create(
            product=product,
            sales_channel_view=view,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product.send(
                sender=assign.__class__,
                instance=assign,
                is_variation=False,
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
            get_import_path(delete_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)

    def test_product_delete_from_product_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="MAG-DEL-PROD-1")

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_product.send(
                sender=product.__class__,
                instance=product,
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
            get_import_path(delete_magento_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)

    def test_property_delete_queues_task(self, *, _unused=None):
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_property = MagentoProperty.objects.create(
            local_instance=property_instance,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_property.send(
                sender=property_instance.__class__,
                instance=property_instance,
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
            get_import_path(delete_magento_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_property.id)

    def test_property_select_value_delete_queues_task(self, *, _unused=None):
        property_instance = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_value = PropertySelectValue.objects.create(
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_property = MagentoProperty.objects.create(
            local_instance=property_instance,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_select_value = MagentoPropertySelectValue.objects.create(
            local_instance=select_value,
            remote_property=remote_property,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            delete_remote_property_select_value.send(
                sender=select_value.__class__,
                instance=select_value,
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
            get_import_path(delete_magento_property_select_value_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_select_value.id)
