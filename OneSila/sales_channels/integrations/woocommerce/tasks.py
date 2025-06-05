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
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel, WoocommerceProduct, WoocommerceProductProperty
from sales_channels.models import RemoteProduct
from orders.models import Order, OrderItem


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_product_db_task(task_queue_item_id, sales_channel_id, product_id):
    from .factories.products import WoocommerceProductCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceProductCreateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import WoocommerceProductPropertyCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceProductPropertyCreateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, product_property_id, remote_product_id
):
    from .factories.properties import WoocommerceProductPropertyUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceProductPropertyUpdateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_product_property_db_task(
    task_queue_item_id, sales_channel_id, remote_product_id, remote_instance_id
):
    from .factories.properties import WoocommerceProductPropertyDeleteFactory

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
        factory = WoocommerceProductPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
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


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_content_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id, language=None
):
    from .factories.products import WoocommerceProductContentUpdateFactory

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


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_eancode_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import WoocommerceEanCodeUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():

        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceEanCodeUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def add_woocommerce_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from .factories.products import WoocommerceProductVariationAddFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        parent = Product.objects.get(id=parent_product_id)
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceProductVariationAddFactory,
            local_instance_id=variation_product_id,
            local_instance_class=Product,
            factory_kwargs={'parent_product': parent},
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def remove_woocommerce_product_variation_db_task(
    task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id
):
    from sales_channels.models import RemoteProduct
    from .factories.products import WoocommerceProductDeleteFactory

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

        factory = WoocommerceProductDeleteFactory(
            sales_channel=sales_channel,
            remote_instance=variant_remote
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.products import WoocommerceMediaProductThroughCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceMediaProductThroughCreateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id
):
    from .factories.products import WoocommerceMediaProductThroughUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceMediaProductThroughUpdateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_woocommerce_image_association_db_task(
    task_queue_item_id, sales_channel_id, remote_instance_id, remote_product_id
):
    from .factories.products import WoocommerceMediaProductThroughDeleteFactory
    from sales_channels.models import RemoteImageProductAssociation
    from sales_channels.integrations.woocommerce.models import WoocommerceProduct

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        remote_inst = RemoteImageProductAssociation.objects.get(id=remote_instance_id)
        factory = WoocommerceMediaProductThroughDeleteFactory(
            sales_channel=sales_channel,
            local_instance=remote_inst.local_instance,
            remote_product=WoocommerceProduct.objects.get(id=remote_product_id),
            remote_instance=remote_inst,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_image_db_task(task_queue_item_id, sales_channel_id, image_id):
    from .factories.products import WoocommerceImageDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_sales_channel_factory(
            sales_channel_id=sales_channel_id,
            factory_class=WoocommerceImageDeleteFactory,
            local_instance_id=image_id,
            local_instance_class=Media,
            sales_channel_class=WoocommerceSalesChannel,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_woocommerce_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import WoocommerceProductUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = WoocommerceProductUpdateFactory(
            sales_channel=WoocommerceSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def sync_woocommerce_product_db_task(
    task_queue_item_id, sales_channel_id, product_id, remote_product_id
):
    from .factories.products import WoocommerceProductSyncFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = WoocommerceProductSyncFactory(
            sales_channel=WoocommerceSalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=RemoteProduct.objects.get(id=remote_product_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_woocommerce_product_db_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.products import WoocommerceProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        factory = WoocommerceProductDeleteFactory(
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


@periodic_task(crontab(minute=0, hour=2))
def woocommerce_pull_remote_orders_db_task():
    from sales_channels.flows.puill_orders import pull_generic_orders_flow
    from .factories.orders import WoocommerceOrderPullFactory

    pull_generic_orders_flow(
        sales_channel_class=WoocommerceSalesChannel,
        factory=WoocommerceOrderPullFactory,
    )


@periodic_task(crontab(minute=0, hour=3))
def cleanup_woocommerce_old_import_data():
    pass
