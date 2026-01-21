from currencies.models import Currency
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation, Product
from properties.models import ProductProperty, Property

from core.tests import TestCase
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.integrations.shein.tasks_receiver_audit import (
    shein__content__update_db_task,
    shein__ean_code__update_db_task,
    shein__image__delete_db_task,
    shein__image_assoc__create_db_task,
    shein__image_assoc__delete_db_task,
    shein__image_assoc__update_db_task,
    shein__price__update_db_task,
    shein__product__update_db_task,
    shein__product_property__create_db_task,
    shein__product_property__delete_db_task,
    shein__product_property__update_db_task,
    shein__variation__add_db_task,
    shein__variation__remove_db_task,
)
from sales_channels.models import SyncRequest
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_image_association,
    create_remote_product_property,
    delete_remote_image,
    delete_remote_image_association,
    delete_remote_product_property,
    remove_remote_product_variation,
    update_remote_image_association,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_eancode,
    update_remote_product_property,
)


class SheinMarketplaceSyncRequestTests(TestCase):
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

    def _assert_sync_request(self, *, sync_type, task_func):
        sync_request = SyncRequest.objects.get(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=None,
            sync_type=sync_type,
        )

        self.assertEqual(sync_request.status, SyncRequest.STATUS_PENDING)
        self.assertEqual(sync_request.task_func_path, get_import_path(task_func))
        self.assertIsNone(sync_request.sales_channel_view_id)
        self.assertEqual(sync_request.task_kwargs.get("remote_product_id"), self.remote_product.id)
        self.assertFalse(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).exists()
        )

    def test_shein_content_update_creates_sync_request(self):
        update_remote_product_content.send(
            sender=self.product.__class__,
            instance=self.product,
            language="en",
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_CONTENT,
            task_func=shein__content__update_db_task,
        )

    def test_shein_price_update_creates_sync_request(self):
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
            task_func=shein__price__update_db_task,
        )

    def test_shein_product_update_creates_sync_request(self):
        update_remote_product.send(
            sender=self.product.__class__,
            instance=self.product,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PRODUCT,
            task_func=shein__product__update_db_task,
        )

    def test_shein_product_property_create_creates_sync_request(self):
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
            task_func=shein__product_property__create_db_task,
        )

    def test_shein_product_property_update_creates_sync_request(self):
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
        update_remote_product_property.send(
            sender=product_property.__class__,
            instance=product_property,
            value_int=6,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=shein__product_property__update_db_task,
        )

    def test_shein_product_property_delete_creates_sync_request(self):
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
            task_func=shein__product_property__delete_db_task,
        )

    def test_shein_variation_add_creates_sync_request(self):
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
            task_func=shein__variation__add_db_task,
        )

    def test_shein_variation_remove_creates_sync_request(self):
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
            task_func=shein__variation__remove_db_task,
        )

    def test_shein_image_assoc_create_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        association = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        create_remote_image_association.send(
            sender=association.__class__,
            instance=association,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=shein__image_assoc__create_db_task,
        )

    def test_shein_image_assoc_update_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        association = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        update_remote_image_association.send(
            sender=association.__class__,
            instance=association,
            extra_payload_key=True,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=shein__image_assoc__update_db_task,
        )

    def test_shein_image_assoc_delete_creates_sync_request(self):
        image = Media.objects.create(
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        association = MediaProductThrough.objects.create(
            product=self.product,
            media=image,
            multi_tenant_company=self.multi_tenant_company,
        )
        delete_remote_image_association.send(
            sender=association.__class__,
            instance=association,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_IMAGES,
            task_func=shein__image_assoc__delete_db_task,
        )

    def test_shein_image_delete_creates_sync_request(self):
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
            sales_channel_view=None,
            sync_type=SyncRequest.TYPE_IMAGES,
        )
        self.assertEqual(sync_request.task_func_path, get_import_path(shein__image__delete_db_task))
        self.assertEqual(sync_request.task_kwargs.get("remote_product_id"), self.remote_product.id)
        self.assertFalse(
            IntegrationTaskQueue.objects.filter(
                integration_id=self.sales_channel.id,
            ).exists()
        )

    def test_shein_ean_code_update_creates_sync_request(self):
        update_remote_product_eancode.send(
            sender=self.product.__class__,
            instance=self.product,
        )

        self._assert_sync_request(
            sync_type=SyncRequest.TYPE_EAN_CODE,
            task_func=shein__ean_code__update_db_task,
        )
