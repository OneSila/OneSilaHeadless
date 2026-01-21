from unittest.mock import patch

from core.signals import mutation_update, post_update
from core.tests import TransactionTestCase
from django.db import transaction
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation, Product
from properties.models import ProductProperty, ProductPropertyTextTranslation, Property
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_image_association,
    create_remote_product,
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

from sales_channels.integrations.shopify.constants import SHOPIFY_TAGS
from sales_channels.integrations.shopify.models import (
    ShopifyImageProductAssociation,
    ShopifyProduct,
    ShopifyProductProperty,
    ShopifySalesChannelView,
)
from sales_channels.integrations.shopify.tasks import (
    add_shopify_product_variation_db_task,
    create_shopify_image_association_db_task,
    create_shopify_product_db_task,
    create_shopify_product_property_db_task,
    delete_shopify_image_association_db_task,
    delete_shopify_image_db_task,
    delete_shopify_product_db_task,
    delete_shopify_product_property_db_task,
    remove_shopify_product_variation_db_task,
    sync_shopify_product_db_task,
    update_shopify_image_association_db_task,
    update_shopify_price_db_task,
    update_shopify_product_content_db_task,
    update_shopify_product_db_task,
    update_shopify_product_eancode_db_task,
    update_shopify_product_property_db_task,
)
from sales_channels.integrations.shopify.tests.mixins import ShopifySalesChannelTestMixin
from sales_channels.models import SalesChannelViewAssign


class ShopifyProductScopedAddReceiverTests(
    TaskQueueDispatchPatchMixin,
    ShopifySalesChannelTestMixin,
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
        remote_product = ShopifyProduct.objects.create(
            local_instance=product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        return product, remote_product

    def test_shopify_content_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-CONT-1")

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
            get_import_path(update_shopify_product_content_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("language"), "en")

    def test_shopify_ean_code_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-EAN-1")

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
            get_import_path(update_shopify_product_eancode_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_image_assoc_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-IMG-1")
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
            get_import_path(create_shopify_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_image_assoc_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-IMG-2")
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
            get_import_path(update_shopify_image_association_db_task),
        )
        self.assertEqual(
            task.task_kwargs.get("media_product_through_id"),
            media_product_through.id,
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_image_assoc_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-IMG-DEL-1")
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
        remote_assoc = ShopifyImageProductAssociation.objects.create(
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
            get_import_path(delete_shopify_image_association_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_assoc.id)

    def test_shopify_price_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-PRICE-1")
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
            get_import_path(update_shopify_price_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("currency_id"), currency.id)

    def test_shopify_product_sync_from_local_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-SYNC-1")

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
            get_import_path(sync_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_product_sync_from_remote_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-SYNC-REMOTE-1")

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
            get_import_path(sync_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_product_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-UPD-1")

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
            get_import_path(update_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_product_property_create_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-PROP-1")
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
            get_import_path(create_shopify_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_product_property_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-PROP-2")
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
            get_import_path(update_shopify_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_property_id"), product_property.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_product_property_delete_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-PROP-DEL-1")
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
        remote_property = ShopifyProductProperty.objects.create(
            local_instance=product_property,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            key="shopify_test_key",
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
            get_import_path(delete_shopify_product_property_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)
        self.assertEqual(task.task_kwargs.get("remote_instance_id"), remote_property.id)

    def test_shopify_product_property_tags_update_queues_task(self, *, _unused=None):

        product, remote_product = self._create_product_and_remote(sku="SHP-TAGS-1")
        property_instance = Property.objects.create(
            type=Property.TYPES.TEXT,
            internal_name=SHOPIFY_TAGS,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language="en",
            value_text="new-tag",
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            post_update.send(
                sender=product_property.__class__,
                instance=product_property,
            )

        self.assertEqual(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).count(),
            initial_count + 2, # + 2 because is doing a proudct_propery update and a product resync
        )

        task = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).latest("id")
        self.assertEqual(
            task.task_name,
            get_import_path(sync_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)

    def test_shopify_variation_add_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-PARENT-1",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-VAR-1",
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
            get_import_path(add_shopify_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_shopify_variation_remove_queues_task(self, *, _unused=None):
        parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-PARENT-2",
            type=Product.CONFIGURABLE,
        )
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-VAR-2",
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
            get_import_path(remove_shopify_product_variation_db_task),
        )
        self.assertEqual(task.task_kwargs.get("parent_product_id"), parent_product.id)
        self.assertEqual(task.task_kwargs.get("variation_product_id"), variation_product.id)

    def test_shopify_product_property_tags_mutation_update_queues_task(self, *, _unused=None):
        product, remote_product = self._create_product_and_remote(sku="SHP-TAGS-2")
        property_instance = Property.objects.create(
            type=Property.TYPES.TEXT,
            internal_name=SHOPIFY_TAGS,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language="en",
            value_text="mutation-tag",
        )

        initial_count = IntegrationTaskQueue.objects.filter(
            integration_id=self.sales_channel.id,
        ).count()

        with patch.object(
            transaction,
            "on_commit",
            side_effect=lambda func, using=None: func(),
        ):
            mutation_update.send(
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
            get_import_path(sync_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)
        self.assertEqual(task.task_kwargs.get("remote_product_id"), remote_product.id)


class ShopifyChannelAddReceiverTests(
    TaskQueueDispatchPatchMixin,
    ShopifySalesChannelTestMixin,
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
        view = ShopifySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            name="Shopify view",
            multi_tenant_company=self.multi_tenant_company,
        )
        return SalesChannelViewAssign.objects.create(
            product=product,
            sales_channel_view=view,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_shopify_product_create_from_assign_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-ASSIGN-1",
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
                view=assign.sales_channel_view
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
            get_import_path(create_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("product_id"), product.id)

    def test_shopify_product_delete_from_assign_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-DEL-ASSIGN-1",
            type=Product.SIMPLE,
        )
        remote_product = ShopifyProduct.objects.create(
            local_instance=product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
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
            get_import_path(delete_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)

    def test_shopify_product_delete_from_product_queues_task(self, *, _unused=None):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SHP-DEL-PROD-1",
            type=Product.SIMPLE,
        )
        remote_product = ShopifyProduct.objects.create(
            local_instance=product,
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
            get_import_path(delete_shopify_product_db_task),
        )
        self.assertEqual(task.task_kwargs.get("remote_instance"), remote_product.id)

    def test_shopify_image_delete_queues_task(self, *, _unused=None):
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
            get_import_path(delete_shopify_image_db_task),
        )
        self.assertEqual(task.task_kwargs.get("image_id"), image.id)
