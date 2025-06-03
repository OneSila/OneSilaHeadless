from huey import crontab
from huey.contrib.djhuey import db_task, periodic_task
from core.huey import HIGH_PRIORITY, MEDIUM_PRIORITY, LOW_PRIORITY
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
from sales_channels.integrations.shopify.models import ShopifySalesChannel, ShopifyProduct, ShopifyProductProperty
from sales_channels.models import RemoteProduct
from orders.models import Order, OrderItem


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_shopify_product_db_task(task_queue_item_id, sales_channel_id, product_id):
    from .factories.products import ShopifyProductCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyProductCreateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_shopify_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import ShopifyProductPropertyCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyProductPropertyCreateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import ShopifyProductPropertyUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyProductPropertyUpdateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_shopify_product_property_db_task(
    task_queue_item_id, sales_channel_id, remote_product_id, remote_instance_id
):
    from .factories.properties import ShopifyProductPropertyDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = ShopifySalesChannel.objects.get(id=sales_channel_id)
        remote_instance = ShopifyProductProperty.objects.get(id=remote_instance_id)

        factory_kwargs = {
            'remote_instance': remote_instance,
            'local_instance': remote_instance.local_instance,
            'sales_channel': sales_channel,
            'remote_product': ShopifyProduct.objects.get(id=remote_product_id)
        }
        factory = ShopifyProductPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_price_db_task(
        task_queue_item_id, sales_channel_id, product_id, remote_product_id, currency_id=None):
    from .factories.prices import ShopifyPriceUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    currency = None
    if currency_id:
        currency = Currency.objects.get(id=currency_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyPriceUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
            factory_kwargs={'currency': currency}
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_product_content_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id, language=None
):
    from .factories.products import ShopifyProductContentUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        factory_kwargs = None
        if language:
            factory_kwargs = {
                'language': language,
            }

        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyProductContentUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
            factory_kwargs=factory_kwargs
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_product_eancode_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import ShopifyEanCodeUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyEanCodeUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def add_shopify_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from .factories.products import ShopifyProductVariationAddFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        parent = Product.objects.get(id=parent_product_id)
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyProductVariationAddFactory,
            local_instance_id=variation_product_id,
            local_instance_class=Product,
            factory_kwargs={'parent_product': parent},
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def remove_shopify_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from sales_channels.models import RemoteProduct
    from .factories.products import ShopifyProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = ShopifySalesChannel.objects.get(id=sales_channel_id)

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

        factory = ShopifyProductDeleteFactory(
            sales_channel=sales_channel,
            remote_instance=variant_remote
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_shopify_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.products import ShopifyMediaProductThroughCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyMediaProductThroughCreateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.products import ShopifyMediaProductThroughUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyMediaProductThroughUpdateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_shopify_image_association_db_task(
    task_queue_item_id, sales_channel_id, remote_instance_id, remote_product_id
):
    from .factories.products import ShopifyMediaProductThroughDeleteFactory
    from sales_channels.models import RemoteImageProductAssociation
    from sales_channels.integrations.shopify.models import ShopifyProduct

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = ShopifySalesChannel.objects.get(id=sales_channel_id)
        remote_inst = RemoteImageProductAssociation.objects.get(id=remote_instance_id)
        factory = ShopifyMediaProductThroughDeleteFactory(
            sales_channel=sales_channel,
            local_instance=remote_inst.local_instance,
            remote_product=ShopifyProduct.objects.get(id=remote_product_id),
            remote_instance=remote_inst,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_shopify_image_db_task(task_queue_item_id, sales_channel_id, image_id):
    from .factories.products import ShopifyImageDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=ShopifyImageDeleteFactory,
            local_instance_id=image_id,
            local_instance_class=Media,
            sales_channel_class=ShopifySalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_shopify_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import ShopifyProductUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        factory = ShopifyProductUpdateFactory(
            sales_channel=ShopifySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def sync_shopify_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import ShopifyProductSyncFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = ShopifyProductSyncFactory(
            sales_channel=ShopifySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_shopify_product_db_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.products import ShopifyProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = ShopifySalesChannel.objects.get(id=sales_channel_id)
        factory = ShopifyProductDeleteFactory(
            sales_channel=sales_channel,
            remote_instance=remote_instance
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=LOW_PRIORITY)
@db_task()
def shopify_import_db_task(import_process, sales_channel):
    from sales_channels.integrations.shopify.factories.imports import ShopifyImportProcessor

    fac = ShopifyImportProcessor(import_process=import_process, sales_channel=sales_channel)
    fac.run()


@periodic_task(crontab(minute=0, hour=2))
def shopify_pull_remote_orders_db_task():
    from sales_channels.flows.puill_orders import pull_generic_orders_flow
    from .factories.orders import ShopifyOrderPullFactory

    pull_generic_orders_flow(
        sales_channel_class=ShopifySalesChannel,
        factory=ShopifyOrderPullFactory,
    )


@periodic_task(crontab(minute=0, hour=3))
def cleanup_old_import_data():
    pass
