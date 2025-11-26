from huey.contrib.djhuey import db_task
from core.huey import HIGH_PRIORITY, MEDIUM_PRIORITY, LOW_PRIORITY, CRUCIAL_PRIORITY
from currencies.models import Currency
from products.models import Product
from media.models import MediaProductThrough, Media
from properties.models import ProductProperty
from sales_channels.decorators import remote_task
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.helpers import (
    run_generic_sales_channel_factory,
    run_remote_product_dependent_sales_channel_factory,
)
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceProduct, WoocommerceProductProperty
from sales_channels.models import RemoteProduct


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_product_db_task(task_queue_item_id, sales_channel_id, product_id):
    from .factories.products import WooCommerceProductCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceProductCreateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: HIGH_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import WooCommerceProductPropertyCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceProductPropertyCreateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: HIGH_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import WooCommerceProductPropertyUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceProductPropertyUpdateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: HIGH_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, remote_product_id, remote_instance_id
):
    from .factories.properties import WooCommerceProductPropertyDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        remote_instance = WoocommerceProductProperty.objects.get(id=remote_instance_id)

        factory_kwargs = {
            'remote_instance': remote_instance,
            'local_instance': remote_instance.local_instance,
            'sales_channel': sales_channel,
            'remote_product': WoocommerceProduct.objects.get(id=remote_product_id)
        }
        factory = WooCommerceProductPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_price_db_task(
        task_queue_item_id, sales_channel_id, product_id, remote_product_id, currency_id=None):
    from .factories.prices import WoocommercePriceUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    currency = None
    if currency_id:
        currency = Currency.objects.get(id=currency_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommercePriceUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
            factory_kwargs={'currency': currency}
        )

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_content_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id, language=None
):
    from .factories.content import WoocommerceProductContentUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        factory_kwargs = None
        if language:
            factory_kwargs = {
                'language': language,
            }

        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceProductContentUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
            factory_kwargs=factory_kwargs
        )

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_eancode_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.ean import WooCommerceEanCodeUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceEanCodeUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: HIGH_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=2)
@db_task()
def add_woocommerce_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from .factories.products import WooCommerceProductVariationAddFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        parent = Product.objects.get(id=parent_product_id)
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceProductVariationAddFactory,
            local_instance_id=variation_product_id,
            local_instance_class=Product,
            factory_kwargs={'parent_product': parent},
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: HIGH_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def remove_woocommerce_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from sales_channels.models import RemoteProduct
    from .factories.products import WooCommerceProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)

        parent_remote = RemoteProduct.objects.get(
            local_instance_id=parent_product_id,
            sales_channel=sales_channel,
            is_variation=False
        )
        variant_remote = RemoteProduct.objects.get(
            local_instance_id=variation_product_id,
            remote_parent_product=parent_remote,
            is_variation=True,
            sales_channel=sales_channel
        )

        factory = WooCommerceProductDeleteFactory(
            sales_channel=sales_channel,
            remote_instance=variant_remote
        )
        factory.run()

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.media import WooCommerceMediaProductThroughCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceMediaProductThroughCreateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.media import WooCommerceMediaProductThroughUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceMediaProductThroughUpdateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)

# Before: MEDIUM_PRIORITY


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, remote_instance_id, remote_product_id
):
    from .factories.media import WooCommerceImageDeleteFactory
    from sales_channels.models import RemoteImageProductAssociation
    from sales_channels.integrations.woocommerce.models import WoocommerceProduct

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        remote_inst = RemoteImageProductAssociation.objects.get(id=remote_instance_id)
        factory = WooCommerceImageDeleteFactory(
            sales_channel=sales_channel,
            local_instance=remote_inst.local_instance,
            remote_product=WoocommerceProduct.objects.get(id=remote_product_id),
            remote_instance=remote_inst,
        )
        factory.run()

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_image_db_task(task_queue_item_id, sales_channel_id, image_id):
    from .factories.media import WooCommerceImageDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WooCommerceImageDeleteFactory,
            local_instance_id=image_id,
            local_instance_class=Media,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import WooCommerceProductUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = WooCommerceProductUpdateFactory(
            sales_channel=WoocommerceSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def sync_woocommerce_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import WooCommerceProductSyncFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = WooCommerceProductSyncFactory(
            sales_channel=WoocommerceSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


# Before: MEDIUM_PRIORITY
@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_product_db_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.products import WooCommerceProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        factory = WooCommerceProductDeleteFactory(
            sales_channel=sales_channel,
            remote_instance=remote_instance
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=LOW_PRIORITY)
@db_task()
def woocommerce_import_db_task(import_process, sales_channel):
    """Run the WooCommerce import process for the given sales channel."""
    from .factories.imports import WoocommerceProductImportProcessor

    fac = WoocommerceProductImportProcessor(
        import_process=import_process,
        sales_channel=sales_channel,
    )
    fac.run()
