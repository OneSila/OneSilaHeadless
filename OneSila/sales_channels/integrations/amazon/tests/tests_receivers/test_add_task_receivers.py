from unittest.mock import patch

from core.tests import TestCase
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import Product, ConfigurableVariation
from properties.models import ProductProperty, Property
from sales_channels.models import SalesChannelViewAssign, SyncRequest
from sales_channels import signals as sc_signals
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_image_association,
    create_remote_product_property,
    delete_remote_image,
    delete_remote_image_association,
    delete_remote_product_property,
    remove_remote_product_variation,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_property, update_remote_image_association,
)

from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView, AmazonProduct
from sales_channels.integrations.amazon.tasks_receiver_audit import (
    amazon__content__update_db_task,
    amazon__image__delete_db_task,
    amazon__image_assoc__create_db_task,
    amazon__image_assoc__delete_db_task,
    amazon__image_assoc__update_db_task,
    amazon__price__update_db_task,
    amazon__product__update_db_task,
    amazon__product_property__create_db_task,
    amazon__product_property__delete_db_task,
    amazon__product_property__update_db_task,
    amazon__variation__add_db_task,
    amazon__variation__remove_db_task,
)


class AmazonMarketplaceSyncRequestTests(TestCase):
    def setUp(self):
        super().setUp()
        self._create_product_signal_patcher = patch.object(
            sc_signals.create_remote_product,
            "send",
            return_value=[],
        )
        self._create_product_signal_patcher.start()
        self.addCleanup(self._create_product_signal_patcher.stop)

        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

    def _assert_sync_request(self, *, sync_type, task_func):
        sync_request = SyncRequest.objects.get(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            sync_type=sync_type,
        )

        self.assertEqual(sync_request.status, SyncRequest.STATUS_PENDING)
        self.assertEqual(sync_request.task_func_path, get_import_path(task_func))
        self.assertEqual(sync_request.task_kwargs.get("sales_channel_view_id"), self.view.id)
        self.assertEqual(sync_request.task_kwargs.get("remote_product_id"), self.remote_product.id)
        self.assertFalse(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).exists()
        )

    def test_amazon_content_update_creates_sync_request(self):
        update_remote_product_content.send(
            sender=self.product.__class__,
            instance=self.product,
            language="en",
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_CONTENT,
            task_func=amazon__content__update_db_task,
        )
    def test_amazon_price_update_creates_sync_request(self):
        currency = Currency.objects.create(
            iso_code="USD",
            name="US Dollar",
            symbol="$",
            multi_tenant_company=self.multi_tenant_company,
        )
        update_remote_price.send(
            sender=self.product.__class__,
            instance=self.product,
            currency=currency,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PRICE,
            task_func=amazon__price__update_db_task,
        )
    def test_amazon_product_update_creates_sync_request(self):
        update_remote_product.send(
            sender=self.product.__class__,
            instance=self.product,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PRODUCT,
            task_func=amazon__product__update_db_task,
        )
    def test_amazon_product_property_create_creates_sync_request(self):
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=property_instance,
            value_int=5,
            multi_tenant_company=self.multi_tenant_company,
        )
        create_remote_product_property.send(
            sender=product_property.__class__,
            instance=product_property,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=amazon__product_property__create_db_task,
        )
    def test_amazon_product_property_update_creates_sync_request(self):
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=property_instance,
            value_int=6,
            multi_tenant_company=self.multi_tenant_company,
        )
        update_remote_product_property.send(
            sender=product_property.__class__,
            instance=product_property,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=amazon__product_property__update_db_task,
        )
    def test_amazon_product_property_delete_creates_sync_request(self):
        property_instance = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=property_instance,
            value_int=7,
            multi_tenant_company=self.multi_tenant_company,
        )
        delete_remote_product_property.send(
            sender=product_property.__class__,
            instance=product_property,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=amazon__product_property__delete_db_task,
        )
    def test_amazon_variation_add_creates_sync_request(self):
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        add_remote_product_variation.send(
            sender=ConfigurableVariation,
            parent_product=self.product,
            variation_product=variation_product,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PRODUCT,
            task_func=amazon__variation__add_db_task,
        )
    def test_amazon_variation_remove_creates_sync_request(self):
        variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        remove_remote_product_variation.send(
            sender=ConfigurableVariation,
            parent_product=self.product,
            variation_product=variation_product,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PRODUCT,
            task_func=amazon__variation__remove_db_task,
        )
    def test_amazon_image_assoc_create_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        create_remote_image_association.send(
            sender=media_product_through.__class__,
            instance=media_product_through,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=amazon__image_assoc__create_db_task,
        )
    def test_amazon_image_assoc_update_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        update_remote_image_association.send(
            sender=media_product_through.__class__,
            instance=media_product_through,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=amazon__image_assoc__update_db_task,
        )
    def test_amazon_image_assoc_delete_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media_product_through = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        delete_remote_image_association.send(
            sender=media_product_through.__class__,
            instance=media_product_through,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=amazon__image_assoc__delete_db_task,
        )

class AmazonImageDeleteSyncRequestTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

    def test_amazon_image_delete_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )

        delete_remote_image.send(
            sender=image.__class__,
            instance=image,
        )

        sync_request = SyncRequest.objects.get(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            sync_type=SyncRequest.TYPE_IMAGES,
        )
        self.assertEqual(sync_request.task_func_path, get_import_path(amazon__image__delete_db_task))
        self.assertEqual(sync_request.task_kwargs.get("remote_product_id"), self.remote_product.id)
        self.assertEqual(sync_request.task_kwargs.get("sales_channel_view_id"), self.view.id)