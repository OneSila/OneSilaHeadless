from huey import crontab
from huey.contrib.djhuey import db_task, periodic_task
from core.huey import HIGH_PRIORITY, LOW_PRIORITY, MEDIUM_PRIORITY
from products.models import Product
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.decorators import remote_task
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.integrations.magento2.factories.properties.properties import MagentoPropertyUpdateFactory
from sales_channels.integrations.magento2.helpers import run_generic_magento_factory, run_remote_product_dependent_magento_factory
from sales_channels.integrations.magento2.models import MagentoSalesChannel, MagentoProduct, MagentoProductProperty, \
    MagentoImageProductAssociation
from sales_channels.models import SalesChannel


# !IMPORTANT: @remote_task needs to be above in order to work
@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_property_db_task(task_queue_item_id, sales_channel_id, property_id):
    from .factories.properties.properties import MagentoPropertyCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertyCreateFactory,
            local_instance_id=property_id,
            local_instance_class=Property
        )

    task.execute(actual_task)


@remote_task(number_of_remote_requests=3)
@db_task()
def update_magento_property_db_task(task_queue_item_id, sales_channel_id, property_id):
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertyUpdateFactory,
            local_instance_id=property_id,
            local_instance_class=Property
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_property_db_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.properties.properties import MagentoPropertyDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance': remote_instance, 'sales_channel': sales_channel}
        factory = MagentoPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_property_select_value_task(task_queue_item_id, sales_channel_id, property_select_value_id):
    from .factories.properties.properties import MagentoPropertySelectValueCreateFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertySelectValueCreateFactory,
            local_instance_id=property_select_value_id,
            local_instance_class=PropertySelectValue
        )

    task.execute(actual_task)


@remote_task(number_of_remote_requests=3)
@db_task()
def update_magento_property_select_value_task(task_queue_item_id, sales_channel_id, property_select_value_id):
    from .factories.properties.properties import MagentoPropertySelectValueUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPropertySelectValueUpdateFactory,
            local_instance_id=property_select_value_id,
            local_instance_class=PropertySelectValue
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_property_select_value_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.properties.properties import MagentoPropertySelectValueDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance': remote_instance, 'sales_channel': sales_channel}
        factory = MagentoPropertySelectValueDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=LOW_PRIORITY, number_of_remote_requests=2)
@db_task()
def pull_magento_sales_channel_views_task(task_queue_item_id, sales_channel_id):
    """
    Task to run the SalesChannelViewPullFactory for a given SalesChannel.
    """
    from .factories.sales_channels.views import MagentoSalesChannelViewPullFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        factory = MagentoSalesChannelViewPullFactory(sales_channel=sales_channel)
        factory.run()

    task.execute(actual_task)

@remote_task(priority=LOW_PRIORITY,number_of_remote_requests=2)
@db_task()
def pull_magento_languages_task(task_queue_item_id, sales_channel_id):
    """
    Task to run the MagentoRemoteLanguage for a given SalesChannel.
    """
    from .factories.sales_channels.languages import MagentoRemoteLanguagePullFactory

    task = BaseRemoteTask(task_queue_item_id)
    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        factory = MagentoRemoteLanguagePullFactory(sales_channel=sales_channel)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY)
@db_task()
def create_magento_attribute_set_task(task_queue_item_id, sales_channel_id, rule_id):
    from .factories.properties.properties import MagentoAttributeSetCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoAttributeSetCreateFactory,
            local_instance_id=rule_id,
            local_instance_class=ProductPropertiesRule
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY)
@db_task()
def update_magento_attribute_set_task(task_queue_item_id, sales_channel_id, rule_id, update_name_only=False):
    from .factories.properties.properties import MagentoAttributeSetUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory_kwargs = {'update_name_only': update_name_only}

        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoAttributeSetUpdateFactory,
            local_instance_id=rule_id,
            local_instance_class=ProductPropertiesRule,
            factory_kwargs=factory_kwargs
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_attribute_set_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.properties.properties import MagentoAttributeSetDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance': remote_instance, 'sales_channel': sales_channel}
        factory = MagentoAttributeSetDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_product_db_task(task_queue_item_id, sales_channel_id, product_id):
    from .factories.products import MagentoProductCreateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoProductCreateFactory,
            local_instance_id=product_id,
            local_instance_class=Product
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_product_property_db_task(task_queue_item_id, sales_channel_id, product_property_id, remote_product_id):
    from .factories.properties import MagentoProductPropertyCreateFactory
    from properties.models import ProductProperty
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoProductPropertyCreateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)


@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_product_property_db_task(task_queue_item_id, sales_channel_id, product_property_id, remote_product_id):
    from .factories.properties import MagentoProductPropertyUpdateFactory
    from properties.models import ProductProperty

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoProductPropertyUpdateFactory,
            local_instance_id=product_property_id,
            local_instance_class=ProductProperty,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_product_property_db_task(task_queue_item_id, sales_channel_id, remote_product_id, remote_instance_id):
    from .factories.properties import MagentoProductPropertyDeleteFactory
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        remote_instance = MagentoProductProperty.objects.get(id=remote_instance_id)

        factory_kwargs = {
            'remote_instance': remote_instance,
            'local_instance': remote_instance.local_instance,
            'sales_channel': sales_channel,
            'remote_product': MagentoProduct.objects.get(id=remote_product_id)
        }
        factory = MagentoProductPropertyDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_price_db_task(task_queue_item_id, sales_channel_id, product_id, remote_product_id):
    from .factories.prices import MagentoPriceUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoPriceUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_product_content_db_task(task_queue_item_id, sales_channel_id, product_id, remote_product_id):
    from .factories.products import MagentoProductContentUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoProductContentUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)

@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_product_eancode_db_task(task_queue_item_id, sales_channel_id, product_id, remote_product_id):
    from .factories.products import MagentoEanCodeUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoEanCodeUpdateFactory,
            local_instance_id=product_id,
            local_instance_class=Product,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=2)
@db_task()
def add_magento_product_variation_db_task(task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id):
    from .factories.products import MagentoProductVariationAddFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        parent_product = Product.objects.get(id=parent_product_id)

        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoProductVariationAddFactory,
            local_instance_id=variation_product_id,
            local_instance_class=Product,
            factory_kwargs={'parent_product': parent_product}
        )

    task.execute(actual_task)

@remote_task(priority=HIGH_PRIORITY, number_of_remote_requests=1)
@db_task()
def remove_magento_product_variation_db_task(task_queue_item_id, sales_channel_id, parent_product_id, variation_product_id):
    from .factories.products import MagentoProductDeleteFactory
    from sales_channels.models import RemoteProduct
    from products.models import Product

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        try:
            # Fetch the remote parent product
            remote_parent_product = RemoteProduct.objects.get(
                local_instance_id=parent_product_id,
                sales_channel_id=sales_channel_id,
                is_variation=False  # Ensure it's a parent product, not a variation
            )

            # Fetch the remote variation product
            remote_variation = RemoteProduct.objects.get(
                local_instance_id=variation_product_id,
                remote_parent_product=remote_parent_product,
                is_variation=True,  # Ensure it's a variation
                sales_channel_id=sales_channel_id
            )

            # Run the factory with the remote variation instance
            run_generic_magento_factory(
                sales_channel_id=sales_channel_id,
                factory_class=MagentoProductDeleteFactory,
                local_instance_id=remote_variation.local_instance_id,
                local_instance_class=Product,
                factory_kwargs={'remote_instance': remote_variation}
            )

        except RemoteProduct.DoesNotExist:
            pass

    task.execute(actual_task)

@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_magento_image_association_db_task(task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id):
    from .factories.products import MagentoMediaProductThroughCreateFactory
    from media.models import MediaProductThrough

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoMediaProductThroughCreateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_image_association_db_task(task_queue_item_id, sales_channel_id, media_product_through_id, remote_product_id):
    from .factories.products import MagentoMediaProductThroughUpdateFactory
    from media.models import MediaProductThrough

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_remote_product_dependent_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoMediaProductThroughUpdateFactory,
            local_instance_id=media_product_through_id,
            local_instance_class=MediaProductThrough,
            remote_product_id=remote_product_id
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_image_association_db_task(task_queue_item_id, sales_channel_id, remote_instance_id, remote_product_id):
    from .factories.products import MagentoMediaProductThroughDeleteFactory
    from sales_channels.integrations.magento2.models import MagentoSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)
        remote_instance = MagentoImageProductAssociation.objects.get(id=remote_instance_id)

        factory_kwargs = {
            'remote_instance':remote_instance,
            'local_instance':remote_instance.local_instance,
            'sales_channel': sales_channel,
            'remote_product': MagentoProduct.objects.get(id=remote_product_id)
        }
        factory = MagentoMediaProductThroughDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)

@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_magento_image_db_task(task_queue_item_id, sales_channel_id, image_id):
    from .factories.products import MagentoImageDeleteFactory
    from media.models import Media

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=MagentoImageDeleteFactory,
            local_instance_id=image_id,
            local_instance_class=Media
        )

    task.execute(actual_task)

@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_magento_product_db_task(task_queue_item_id, sales_channel_id, product_id, remote_product_id):
    from .factories.products import MagentoProductUpdateFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = MagentoProductUpdateFactory(
            sales_channel=SalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=MagentoProduct.objects.get(id=remote_product_id)
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=1)
@db_task()
def sync_magento_product_db_task(task_queue_item_id, sales_channel_id, product_id, remote_product_id):
    from .factories.products import MagentoProductSyncFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        factory = MagentoProductSyncFactory(
            sales_channel=SalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=MagentoProduct.objects.get(id=remote_product_id)
        )
        factory.run()


    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def update_magento_sales_view_assign_db_task(task_queue_item_id, sales_channel_id, assign_id):
    from .factories.products import RemoteSalesChannelAssignUpdateFactory
    from sales_channels.models import SalesChannelViewAssign

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        run_generic_magento_factory(
            sales_channel_id=sales_channel_id,
            factory_class=RemoteSalesChannelAssignUpdateFactory,
            local_instance_id=assign_id,
            local_instance_class=SalesChannelViewAssign
        )

    task.execute(actual_task)

@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=2)
@db_task()
def delete_magento_product_db_task(task_queue_item_id, sales_channel_id, remote_instance):
    from .factories.products import MagentoProductDeleteFactory

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = MagentoSalesChannel.objects.get(id=sales_channel_id)

        factory_kwargs = {'remote_instance': remote_instance, 'sales_channel': sales_channel}
        factory = MagentoProductDeleteFactory(**factory_kwargs)
        factory.run()

    task.execute(actual_task)

@db_task()
def magento_import_db_task(import_process, sales_channel):
    from sales_channels.integrations.magento2.factories.imports import MagentoImportProcessor

    fac = MagentoImportProcessor(import_process=import_process, sales_channel=sales_channel)
    fac.run()

@periodic_task(crontab(minute=0, hour=2))
def magento_pull_remote_orders_db_task():
    from .flows.puill_orders import pull_magento_orders_flow

    pull_magento_orders_flow()


@periodic_task(crontab(minute=0, hour=3))
def cleanup_old_import_data():
    from .flows.cleanup_import_logs import cleanup_import_logs_flow

    cleanup_import_logs_flow()