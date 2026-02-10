from unittest.mock import patch

from core.tests import TransactionTestCase
from django.db import transaction
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation, Product
from properties.models import ProductProperty, Property
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_product,
    create_remote_image_association,
    create_remote_product_property,
    delete_remote_image,
    delete_remote_image_association,
    delete_remote_product,
    delete_remote_product_property,
    remove_remote_product_variation,
    sync_remote_product,
    update_remote_image_association,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_eancode,
    update_remote_product_property,
)
from sales_channels.tests.helpers import TaskQueueDispatchPatchMixin

from sales_channels.integrations.woocommerce.models import (
    WoocommerceMediaThroughProduct,
    WoocommerceProduct,
    WoocommerceProductProperty,
    WoocommerceSalesChannelView,
)
from sales_channels.integrations.woocommerce.tasks import (
    add_woocommerce_product_variation_db_task,
    create_woocommerce_product_db_task,
    create_woocommerce_image_association_db_task,
    create_woocommerce_product_property_db_task,
    delete_woocommerce_image_association_db_task,
    delete_woocommerce_image_db_task,
    delete_woocommerce_product_db_task,
    delete_woocommerce_product_property_db_task,
    remove_woocommerce_product_variation_db_task,
    sync_woocommerce_product_db_task,
    update_woocommerce_image_association_db_task,
    update_woocommerce_price_db_task,
    update_woocommerce_product_content_db_task,
    update_woocommerce_product_db_task,
    update_woocommerce_product_eancode_db_task,
    update_woocommerce_product_property_db_task,
)
from sales_channels.integrations.woocommerce.tests.mixins import WooCommerceSalesChannelTestMixin
from sales_channels.models import SalesChannelViewAssign


class WooCommerceProductScopedAddReceiverTests(
    TaskQueueDispatchPatchMixin,
    WooCommerceSalesChannelTestMixin,
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
        remote_product = WoocommerceProduct.objects.create(
            local_instance=product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        return product, remote_product

    def test_woocommerce_content_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-CONT-1")

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
            get_import_path(update_woocommerce_product_content_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_woocommerce_ean_code_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-EAN-1")

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
            get_import_path(update_woocommerce_product_eancode_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_image_assoc_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-IMG-1")
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
            get_import_path(create_woocommerce_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_image_assoc_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-IMG-2")
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
            get_import_path(update_woocommerce_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_price_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-PRICE-1")
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
            get_import_path(update_woocommerce_price_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("currency_id"), currency.id)

    def test_woocommerce_product_sync_from_local_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-SYNC-1")

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
            get_import_path(sync_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_product_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-UPD-1")

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
            get_import_path(update_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_product_property_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-PROP-1")
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
            get_import_path(create_woocommerce_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_product_property_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-PROP-2")
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
            get_import_path(update_woocommerce_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_product_property_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-PROP-DEL-1")
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
        remote_property = WoocommerceProductProperty.objects.create(
            local_instance=product_property,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
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
            get_import_path(delete_woocommerce_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_property.id)

    def test_woocommerce_image_assoc_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-IMG-DEL-1")
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
        remote_assoc = WoocommerceMediaThroughProduct.objects.create(
            local_instance=media_product_through,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
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
            get_import_path(delete_woocommerce_image_association_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_assoc.id)

    def test_woocommerce_product_sync_from_remote_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-SYNC-REMOTE-1")

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
            get_import_path(sync_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_woocommerce_product_delete_from_assign_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-DEL-ASSIGN-1")
        view = WoocommerceSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Woo view",
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
                sender=SalesChannelViewAssign,
                instance=assign,
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
            get_import_path(delete_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)

    def test_woocommerce_product_delete_from_product_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="WOO-DEL-PROD-1")

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
            get_import_path(delete_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)


class WooCommerceChannelAddReceiverTests(
    TaskQueueDispatchPatchMixin,
    WooCommerceSalesChannelTestMixin,
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

    def _create_view_assign(self, *, product):
        view = WoocommerceSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Woo view",
        )
        return SalesChannelViewAssign.objects.create(
            product=product,
            sales_channel_view=view,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )

    def test_woocommerce_product_create_from_assign_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="WOO-ASSIGN-1",
            type=Product.SIMPLE,
        )
        assign = self._create_view_assign(product=product)

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            create_remote_product.send(
                sender=SalesChannelViewAssign,
                instance=assign,
                view=assign.sales_channel_view,
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
            get_import_path(create_woocommerce_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)

    def test_woocommerce_variation_add_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="WOO-PARENT-1",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="WOO-VAR-1",
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
            get_import_path(add_woocommerce_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_woocommerce_variation_remove_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="WOO-PARENT-2",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="WOO-VAR-2",
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
            get_import_path(remove_woocommerce_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_woocommerce_image_delete_queues_task(self, *, _unused=None):
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
            get_import_path(delete_woocommerce_image_db_task),
        )
        self.assertEqual(task.task_kwargs.get("image_id"), image.id)
