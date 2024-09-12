from django.db.models.signals import pre_delete
from django.dispatch import receiver

from orders.signals import to_ship, shipped, hold, cancelled
from properties.signals import product_properties_rule_created, product_properties_rule_updated, product_properties_rule_rename
from sales_channels.integrations.magento2.flows.default import run_generic_magento_task_flow, run_delete_generic_magento_task_flow
from sales_channels.integrations.magento2.models import MagentoProperty
from sales_channels.signals import create_remote_property, update_remote_property, delete_remote_property, create_remote_property_select_value, \
    update_remote_property_select_value, delete_remote_property_select_value, refresh_website_pull_models, sales_channel_created


@receiver(create_remote_property, sender='properties.Property')
def sales_channels__magento__property__create(sender, instance, **kwargs):
    """
    Handles the create signal for properties specifically for Magento integration.
    Runs the MagentoPropertyCreateFactory using the run_generic_magento_task function.
    """
    from .tasks import create_magento_property_db_task

    task_kwargs = {'property_id': instance.id}
    run_generic_magento_task_flow(create_magento_property_db_task, **task_kwargs)

@receiver(update_remote_property, sender='properties.Property')
def sales_channels__magento__property__update(sender, instance, **kwargs):
    """
    Handles the update signal for properties specifically for Magento integration.
    """
    from .tasks import update_magento_property_db_task

    task_kwargs = {'property_id': instance.id}
    run_generic_magento_task_flow(update_magento_property_db_task, **task_kwargs)


@receiver(delete_remote_property, sender='properties.Property')
def sales_channels__magento__property__delete(sender, instance, **kwargs):
    """
    Handles the delete signal for properties specifically for Magento integration.
    """
    from .tasks import delete_magento_property_db_task

    task_kwargs = {'local_instance_id': instance.id}
    run_delete_generic_magento_task_flow(task_func=delete_magento_property_db_task, remote_class=MagentoProperty, **task_kwargs)


@receiver(create_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__create(sender, instance, **kwargs):
    """
    Handles the create signal for PropertySelectValue specifically for Magento integration.
    """
    from .tasks import create_magento_property_select_value_task

    task_kwargs = {'property_select_value_id': instance.id}
    run_generic_magento_task_flow(create_magento_property_select_value_task, **task_kwargs)


@receiver(update_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__update(sender, instance, **kwargs):
    """
    Handles the update signal for PropertySelectValue specifically for Magento integration.
    """
    from .tasks import update_magento_property_select_value_task


    task_kwargs = {'property_select_value_id': instance.id}
    run_generic_magento_task_flow(update_magento_property_select_value_task, **task_kwargs)


@receiver(delete_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__delete(sender, instance, **kwargs):
    """
    Handles the delete signal for PropertySelectValue specifically for Magento integration.
    """
    from .tasks import delete_magento_property_select_value_task
    from .models import MagentoPropertySelectValue

    task_kwargs = {'local_instance_id': instance.id}
    run_delete_generic_magento_task_flow(
        task_func=delete_magento_property_select_value_task,
        remote_class=MagentoPropertySelectValue,
        **task_kwargs
    )

@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
def sales_channels__magento__handle_pull_magento_sales_chjannel_views(sender, instance, **kwargs):
    """
    Handles the refresh_website_pull_models and sales_channel_created signals for Magento integration.
    Enqueues a task to pull Magento sales channel views for the sales channel.
    """
    from sales_channels.tasks import add_task_to_queue
    from sales_channels.helpers import get_import_path
    from .tasks import pull_magento_sales_channel_views_task, pull_magento_languages_task

    task_kwargs = {'sales_channel_id': instance.id}
    add_task_to_queue(
        sales_channel_id=instance.id,
        task_func_path=get_import_path(pull_magento_sales_channel_views_task),
        task_kwargs=task_kwargs,
    )
    add_task_to_queue(
        sales_channel_id=instance.id,
        task_func_path=get_import_path(pull_magento_languages_task),
        task_kwargs=task_kwargs,
    )


@receiver(product_properties_rule_created, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__create(sender, instance, **kwargs):
    """
    Handles the create signal for ProductPropertiesRule specifically for Magento integration.
    Runs the MagentoAttributeSetCreateFactory using the run_generic_magento_task_flow function.
    """
    from .tasks import create_magento_attribute_set_task

    task_kwargs = {'rule_id': instance.id}
    run_generic_magento_task_flow(create_magento_attribute_set_task,number_of_remote_requests=instance.items.all().count() + 1, **task_kwargs)

@receiver(product_properties_rule_updated, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__update(sender, instance, **kwargs):
    """
    Handles the update signal for ProductPropertiesRule specifically for Magento integration.
    Runs the MagentoAttributeSetUpdateFactory using the run_generic_magento_task_flow function.
    """
    from .tasks import update_magento_attribute_set_task

    task_kwargs = {'rule_id': instance.id}
    run_generic_magento_task_flow(update_magento_attribute_set_task, number_of_remote_requests=instance.items.all().count(), **task_kwargs)

@receiver(product_properties_rule_rename, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__rename(sender, instance, **kwargs):
    """
    Handles the rename signal for ProductPropertiesRule specifically for Magento integration.
    Runs the MagentoAttributeSetUpdateFactory with update_name_only=True using the run_generic_magento_task_flow function.
    """
    from .tasks import update_magento_attribute_set_task

    task_kwargs = {
        'rule_id': instance.id,
        'update_name_only': True
    }

    run_generic_magento_task_flow(
        task_func=update_magento_attribute_set_task,
        number_of_remote_requests=2,
        **task_kwargs
    )

@receiver(pre_delete, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__delete(sender, instance, **kwargs):
    """
    Handles the delete signal for ProductPropertiesRule specifically for Magento integration.
    Runs the MagentoAttributeSetDeleteFactory using the run_delete_generic_magento_task_flow function.
    """
    from .tasks import delete_magento_attribute_set_task
    from .models.property import MagentoAttributeSet

    task_kwargs = {'local_instance_id': instance.id}
    run_delete_generic_magento_task_flow(
        task_func=delete_magento_attribute_set_task,
        remote_class=MagentoAttributeSet,
        **task_kwargs
    )


@receiver(to_ship, sender='orders.Order')
@receiver(shipped, sender='orders.Order')
@receiver(hold, sender='orders.Order')
@receiver(cancelled, sender='orders.Order')
def sales_channels__magento__order_status__update(sender, instance, **kwargs):
    """
    Handles the status update signals for orders specifically for Magento integration.
    """
    from .tasks import update_magento_order_status_db_task


    task_kwargs = {
        'order_id': instance.id,
    }

    run_generic_magento_task_flow(update_magento_order_status_db_task, **task_kwargs)