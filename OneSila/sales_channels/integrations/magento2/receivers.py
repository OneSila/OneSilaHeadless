from django.db.models.signals import pre_delete
from django.dispatch import receiver

from orders.signals import to_ship, shipped, hold, cancelled
from properties.signals import product_properties_rule_created, product_properties_rule_updated, product_properties_rule_rename
from sales_channels.integrations.magento2.flows.default import run_generic_magento_task_flow, run_delete_generic_magento_task_flow, \
    run_product_specific_magento_task_flow, run_delete_product_specific_generic_magento_task_flow
from sales_channels.integrations.magento2.models import MagentoProperty
from sales_channels.signals import create_remote_property, update_remote_property, delete_remote_property, \
    create_remote_property_select_value, \
    update_remote_property_select_value, delete_remote_property_select_value, refresh_website_pull_models, \
    sales_channel_created, create_remote_product, \
    create_remote_product_property, update_remote_product_property, delete_remote_product_property, \
    update_remote_inventory, update_remote_price, \
    update_remote_product_content, add_remote_product_variation, remove_remote_product_variation, \
    create_remote_image_association, \
    update_remote_image_association, delete_remote_image_association, delete_remote_image, update_remote_product, \
    sync_remote_product, \
    sales_view_assign_updated, delete_remote_product, update_remote_product_eancode


@receiver(create_remote_property, sender='properties.Property')
def sales_channels__magento__property__create(sender, instance, **kwargs):
    from .tasks import create_magento_property_db_task

    task_kwargs = {'property_id': instance.id}
    run_generic_magento_task_flow(create_magento_property_db_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)

@receiver(update_remote_property, sender='properties.Property')
def sales_channels__magento__property__update(sender, instance, **kwargs):
    from .tasks import update_magento_property_db_task

    task_kwargs = {'property_id': instance.id}
    run_generic_magento_task_flow(update_magento_property_db_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)


@receiver(delete_remote_property, sender='properties.Property')
def sales_channels__magento__property__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_property_db_task

    run_delete_generic_magento_task_flow(
        task_func=delete_magento_property_db_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=MagentoProperty)


@receiver(create_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__create(sender, instance, **kwargs):
    from .tasks import create_magento_property_select_value_task

    task_kwargs = {'property_select_value_id': instance.id}
    run_generic_magento_task_flow(create_magento_property_select_value_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)


@receiver(update_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__update(sender, instance, **kwargs):
    from .tasks import update_magento_property_select_value_task


    task_kwargs = {'property_select_value_id': instance.id}
    run_generic_magento_task_flow(update_magento_property_select_value_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)


@receiver(delete_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_property_select_value_task
    from .models import MagentoPropertySelectValue

    run_delete_generic_magento_task_flow(
        task_func=delete_magento_property_select_value_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=MagentoPropertySelectValue,
    )

@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='magento2.MagentoSalesChannel')
@receiver(sales_channel_created, sender='magento2.MagentoSalesChannel')
def sales_channels__magento__handle_pull_magento_sales_chjannel_views(sender, instance, **kwargs):
    from integrations.tasks import add_task_to_queue
    from integrations.helpers import get_import_path
    from .tasks import pull_magento_sales_channel_views_task, pull_magento_languages_task

    task_kwargs = {'sales_channel_id': instance.id}
    add_task_to_queue(
        integration_id=instance.id,
        task_func_path=get_import_path(pull_magento_sales_channel_views_task),
        task_kwargs=task_kwargs,
    )
    add_task_to_queue(
        integration_id=instance.id,
        task_func_path=get_import_path(pull_magento_languages_task),
        task_kwargs=task_kwargs,
    )


@receiver(product_properties_rule_created, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__create(sender, instance, **kwargs):
    from .tasks import create_magento_attribute_set_task

    task_kwargs = {'rule_id': instance.id}
    run_generic_magento_task_flow(create_magento_attribute_set_task, multi_tenant_company=instance.multi_tenant_company, number_of_remote_requests=instance.items.all().count() + 1, **task_kwargs)

@receiver(product_properties_rule_updated, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__update(sender, instance, **kwargs):
    from .tasks import update_magento_attribute_set_task

    task_kwargs = {'rule_id': instance.id}
    run_generic_magento_task_flow(update_magento_attribute_set_task, multi_tenant_company=instance.multi_tenant_company, number_of_remote_requests=instance.items.all().count(), **task_kwargs)

@receiver(product_properties_rule_rename, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__rename(sender, instance, **kwargs):
    from .tasks import update_magento_attribute_set_task

    task_kwargs = {
        'rule_id': instance.id,
        'update_name_only': True
    }

    run_generic_magento_task_flow(
        task_func=update_magento_attribute_set_task,
        multi_tenant_company=instance.multi_tenant_company,
        number_of_remote_requests=2,
        **task_kwargs
    )

@receiver(pre_delete, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_attribute_set_task
    from .models.properties import MagentoAttributeSet

    run_delete_generic_magento_task_flow(
        task_func=delete_magento_attribute_set_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=MagentoAttributeSet,
    )


@receiver(create_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__create(sender, instance, **kwargs):
    from .tasks import create_magento_product_property_db_task

    task_kwargs = {'product_property_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=create_magento_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        **task_kwargs)

@receiver(update_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_property_db_task

    task_kwargs = {'product_property_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        **task_kwargs)

@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_product_property_db_task
    from .models import MagentoProductProperty

    run_delete_product_specific_generic_magento_task_flow(
        task_func=delete_magento_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=MagentoProductProperty,
        local_instance_id=instance.id,
        product=instance.product)

# @receiver(update_remote_inventory, sender='products.Product')
# def sales_channels__magento__inventory__update(sender, instance, **kwargs):
#     from .tasks import update_magento_inventory_db_task
#
#     task_kwargs = {'product_id': instance.id}
#     run_product_specific_magento_task_flow(
#         task_func=update_magento_inventory_db_task,
#         multi_tenant_company=instance.multi_tenant_company,
#         product=instance,
#         **task_kwargs)

@receiver(update_remote_price, sender='products.Product')
def sales_channels__magento__price__update(sender, instance, **kwargs):
    from .tasks import update_magento_price_db_task

    task_kwargs = {'product_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_price_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        **task_kwargs)

@receiver(update_remote_product_content, sender='products.Product')
def sales_channels__magento__product_content__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_content_db_task

    task_kwargs = {'product_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_product_content_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        **task_kwargs)

@receiver(update_remote_product_eancode, sender='products.Product')
def sales_channels__magento__product_eancode__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_eancode_db_task

    task_kwargs = {'product_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_product_eancode_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        **task_kwargs)

@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def sales_channels__magento__product_variation__add(sender, parent_product, variation_product, **kwargs):
    from .tasks import add_magento_product_variation_db_task

    task_kwargs = {
        'parent_product_id': parent_product.id,
        'variation_product_id': variation_product.id
    }
    run_generic_magento_task_flow(add_magento_product_variation_db_task, multi_tenant_company=parent_product.multi_tenant_company, **task_kwargs)

@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def sales_channels__magento__product_variation__remove(sender, parent_product, variation_product, **kwargs):
    """
    Handles the removal of product variations in Magento.
    """
    from .tasks import remove_magento_product_variation_db_task

    task_kwargs = {
        'parent_product_id': parent_product.id,
        'variation_product_id': variation_product.id
    }
    run_generic_magento_task_flow(remove_magento_product_variation_db_task, multi_tenant_company=parent_product.multi_tenant_company, **task_kwargs)

@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__create(sender, instance, **kwargs):
    from .tasks import create_magento_image_association_db_task

    task_kwargs = {'media_product_through_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=create_magento_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        **task_kwargs)

@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__update(sender, instance, **kwargs):
    from .tasks import update_magento_image_association_db_task

    task_kwargs = {'media_product_through_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        **task_kwargs)

@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_image_association_db_task
    from .models import MagentoImageProductAssociation

    run_delete_product_specific_generic_magento_task_flow(
        task_func=delete_magento_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=MagentoImageProductAssociation,
        local_instance_id=instance.id,
        product=instance.product
    )


@receiver(delete_remote_image, sender='media.Media')
def sales_channels__magento__image__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_image_db_task

    task_kwargs = {'image_id': instance.id}
    run_generic_magento_task_flow(delete_magento_image_db_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)

@receiver(update_remote_product, sender='products.Product')
def sales_channels__magento__product__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_db_task

    task_kwargs = {'product_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=update_magento_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        **task_kwargs)

@receiver(sync_remote_product, sender='products.Product')
def sales_channels__magento__product__sync(sender, instance, **kwargs):
    from .tasks import sync_magento_product_db_task
    from products.product_types import CONFIGURABLE

    if instance.type == CONFIGURABLE:
        number_of_remote_requests = 1 + instance.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_kwargs = {'product_id': instance.id}
    run_product_specific_magento_task_flow(
        task_func=sync_magento_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=number_of_remote_requests,
        **task_kwargs)


@receiver(sales_view_assign_updated, sender='products.Product')
def sales_channels__magento__assign__update(sender, instance, **kwargs):
    from .tasks import update_magento_sales_view_assign_db_task

    task_kwargs = {'assign_id': instance.id}
    run_generic_magento_task_flow(update_magento_sales_view_assign_db_task, multi_tenant_company=instance.multi_tenant_company, **task_kwargs)

@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def sales_channels__magento__product__create(sender, instance, **kwargs):
    from .tasks import create_magento_product_db_task
    from products.product_types import CONFIGURABLE
    product = instance.product
    sales_channel = instance.sales_channel

    if product.type == CONFIGURABLE:
        number_of_remote_requests = 1 + product.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_kwargs = {'product_id': product.id}
    run_generic_magento_task_flow(
        task_func=create_magento_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        number_of_remote_requests=number_of_remote_requests,
        sales_channels_filter_kwargs={'id': sales_channel.id},
        **task_kwargs)

@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def sales_channels__magento__product__delete_from_assign(sender, instance, **kwargs):
    from .tasks import delete_magento_product_db_task
    from .models.products import MagentoProduct

    product = instance.product
    sales_channel = instance.sales_channel

    run_delete_generic_magento_task_flow(
        task_func=delete_magento_product_db_task,
        local_instance_id=product.id,
        remote_class=MagentoProduct,
        multi_tenant_company=product.multi_tenant_company,
        sales_channels_filter_kwargs={'id': sales_channel.id},
        is_variation=kwargs.get('is_variation', False)
    )


@receiver(delete_remote_product, sender='products.Product')
def sales_channels__magento__product__delete_from_product(sender, instance, **kwargs):
    from .tasks import delete_magento_product_db_task
    from .models.products import MagentoProduct

    run_delete_generic_magento_task_flow(
        task_func=delete_magento_product_db_task,
        local_instance_id=instance.id,
        remote_class=MagentoProduct,
        multi_tenant_company=instance.multi_tenant_company,
        is_multiple=True
    )
