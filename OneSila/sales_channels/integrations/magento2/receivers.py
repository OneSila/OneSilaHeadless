from django.db.models.signals import pre_delete
from django.dispatch import receiver

from properties.signals import product_properties_rule_created, product_properties_rule_updated, product_properties_rule_rename
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.helpers import rebind_magento_attribute_sets_for_rule
from sales_channels.signals import update_remote_property, delete_remote_property, \
    update_remote_property_select_value, delete_remote_property_select_value, refresh_website_pull_models, \
    sales_channel_created, create_remote_product, \
    create_remote_product_property, update_remote_product_property, delete_remote_product_property, \
    update_remote_price, \
    update_remote_product_content, add_remote_product_variation, remove_remote_product_variation, \
    create_remote_image_association, \
    update_remote_image_association, delete_remote_image_association, delete_remote_image, update_remote_product, \
    sync_remote_product, manual_sync_remote_product, \
    sales_view_assign_updated, delete_remote_product, update_remote_product_eancode, update_remote_vat_rate, \
    create_remote_vat_rate


# Magento properties are created only when needed by product/property sync.


@receiver(update_remote_property, sender='properties.Property')
def sales_channels__magento__property__update(sender, instance, **kwargs):
    from .tasks import update_magento_property_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask
    language = kwargs.get('language', None)

    task_runner = MagentoChannelAddTask(
        task_func=update_magento_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(property_id=instance.id, language=language)
    task_runner.run()


@receiver(delete_remote_property, sender='properties.Property')
def sales_channels__magento__property__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_property_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoPropertyDeleteAddTask

    task_runner = MagentoPropertyDeleteAddTask(
        task_func=delete_magento_property_db_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.run()


# Magento select values are created only when needed by product/property sync.


@receiver(update_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__update(sender, instance, **kwargs):
    from .tasks import update_magento_property_select_value_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask
    language = kwargs.get('language', None)

    task_runner = MagentoChannelAddTask(
        task_func=update_magento_property_select_value_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(property_select_value_id=instance.id, language=language)
    task_runner.run()


@receiver(delete_remote_property_select_value, sender='properties.PropertySelectValue')
def sales_channels__magento__property_select_value__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_property_select_value_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoPropertySelectValueDeleteAddTask

    task_runner = MagentoPropertySelectValueDeleteAddTask(
        task_func=delete_magento_property_select_value_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.run()


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='magento2.MagentoSalesChannel')
@receiver(sales_channel_created, sender='magento2.MagentoSalesChannel')
def sales_channels__magento__handle_pull_magento_sales_chjannel_views(sender, instance, **kwargs):
    from sales_channels.integrations.magento2.factories.sales_channels.views import MagentoSalesChannelViewPullFactory
    from sales_channels.integrations.magento2.factories.sales_channels.languages import MagentoRemoteLanguagePullFactory

    if not isinstance(instance.get_real_instance(), MagentoSalesChannel):
        return

    views_factory = MagentoSalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = MagentoRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()


@receiver(product_properties_rule_created, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__create(sender, instance, **kwargs):
    if instance.sales_channel_id:
        return

    from .tasks import create_magento_attribute_set_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=create_magento_attribute_set_task,
        multi_tenant_company=instance.multi_tenant_company,
        number_of_remote_requests=instance.items.all().count() + 1,
    )
    task_runner.set_extra_task_kwargs(rule_id=instance.id)
    task_runner.run()


@receiver(product_properties_rule_updated, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__update(sender, instance, **kwargs):
    from .tasks import update_magento_attribute_set_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoRuleScopedAddTask

    task_runner = MagentoRuleScopedAddTask(
        task_func=update_magento_attribute_set_task,
        rule=instance,
        number_of_remote_requests=instance.items.all().count(),
    )
    task_runner.set_extra_task_kwargs(rule_id=instance.id)
    task_runner.run()


@receiver(product_properties_rule_rename, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__rename(sender, instance, **kwargs):
    from .tasks import update_magento_attribute_set_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoRuleScopedAddTask

    task_kwargs = {
        'rule_id': instance.id,
        'update_name_only': True
    }

    task_runner = MagentoRuleScopedAddTask(
        task_func=update_magento_attribute_set_task,
        rule=instance,
        number_of_remote_requests=2,
    )
    task_runner.set_extra_task_kwargs(**task_kwargs)
    task_runner.run()


@receiver(pre_delete, sender='properties.ProductPropertiesRule')
def sales_channels__magento__attribute_set__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_attribute_set_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoAttributeSetDeleteAddTask

    task_runner = MagentoAttributeSetDeleteAddTask(
        task_func=delete_magento_attribute_set_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.run()


@receiver(create_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__create(sender, instance, **kwargs):
    from .tasks import create_magento_product_property_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPropertyAddTask
    language = kwargs.get('language', None)

    task_runner = MagentoProductPropertyAddTask(
        task_func=create_magento_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(
        product_property_id=instance.id,
        language=language,
    )
    task_runner.run()


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_property_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPropertyAddTask
    language = kwargs.get('language', None)

    task_runner = MagentoProductPropertyAddTask(
        task_func=update_magento_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(
        product_property_id=instance.id,
        language=language,
    )
    task_runner.run()


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def sales_channels__magento__product_property__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_product_property_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPropertyDeleteAddTask

    task_runner = MagentoProductPropertyDeleteAddTask(
        task_func=delete_magento_product_property_db_task,
        product=instance.product,
        local_instance_id=instance.id,
    )
    task_runner.run()

# @receiver(update_remote_inventory, sender='products.Product')
# def sales_channels__magento__inventory__update(sender, instance, **kwargs):
#     from .tasks import update_magento_inventory_db_task
#
#     task_kwargs = {'product_id': instance.id}
#     run_product_specific_sales_channel_task_flow(
#         task_func=update_magento_inventory_db_task,
#         multi_tenant_company=instance.multi_tenant_company,
#         product=instance,
#         **task_kwargs)


@receiver(update_remote_price, sender='products.Product')
def sales_channels__magento__price__update(sender, instance, **kwargs):
    from .tasks import update_magento_price_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductPriceAddTask
    currency = kwargs.get('currency', None)

    task_runner = MagentoProductPriceAddTask(
        task_func=update_magento_price_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(
        product_id=instance.id,
        currency_id=currency.id,
    )
    task_runner.run()


@receiver(update_remote_product_content, sender='products.Product')
def sales_channels__magento__product_content__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_content_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductContentAddTask
    language = kwargs.get('language', None)

    task_runner = MagentoProductContentAddTask(
        task_func=update_magento_product_content_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(
        product_id=instance.id,
        language=language,
    )
    task_runner.run()


@receiver(update_remote_product_eancode, sender='products.Product')
def sales_channels__magento__product_eancode__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_eancode_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductEanCodeAddTask

    task_runner = MagentoProductEanCodeAddTask(
        task_func=update_magento_product_eancode_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def sales_channels__magento__product_variation__add(sender, parent_product, variation_product, **kwargs):
    from .tasks import add_magento_product_variation_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=add_magento_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )
    task_runner.run()


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def sales_channels__magento__product_variation__remove(sender, parent_product, variation_product, **kwargs):
    """
    Handles the removal of product variations in Magento.
    """
    from .tasks import remove_magento_product_variation_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=remove_magento_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )
    task_runner.run()


@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__create(sender, instance, **kwargs):
    from .tasks import create_magento_image_association_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductImagesAddTask

    task_runner = MagentoProductImagesAddTask(
        task_func=create_magento_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__update(sender, instance, **kwargs):
    from .tasks import update_magento_image_association_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductImagesAddTask

    task_runner = MagentoProductImagesAddTask(
        task_func=update_magento_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def sales_channels__magento__media_product_through__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_image_association_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoImageAssociationDeleteAddTask

    task_runner = MagentoImageAssociationDeleteAddTask(
        task_func=delete_magento_image_association_db_task,
        product=instance.product,
        local_instance_id=instance.id,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.run()


@receiver(delete_remote_image, sender='media.Media')
def sales_channels__magento__image__delete(sender, instance, **kwargs):
    from .tasks import delete_magento_image_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=delete_magento_image_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(image_id=instance.id)
    task_runner.run()


@receiver(update_remote_product, sender='products.Product')
def sales_channels__magento__product__update(sender, instance, **kwargs):
    from .tasks import update_magento_product_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductUpdateAddTask

    task_runner = MagentoProductUpdateAddTask(
        task_func=update_magento_product_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(sync_remote_product, sender='products.Product')
@receiver(manual_sync_remote_product, sender='products.Product')
def sales_channels__magento__product__sync_from_product(sender, instance, **kwargs):
    from .tasks import sync_magento_product_db_task
    from products.product_types import CONFIGURABLE
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductFullSyncAddTask

    if instance.type == CONFIGURABLE:
        number_of_remote_requests = 1 + instance.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_runner = MagentoProductFullSyncAddTask(
        task_func=sync_magento_product_db_task,
        product=instance,
        number_of_remote_requests=number_of_remote_requests,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(sync_remote_product, sender='sales_channels.RemoteProduct')
@receiver(sync_remote_product, sender='magento2.MagentoProduct')
@receiver(manual_sync_remote_product, sender='sales_channels.RemoteProduct')
@receiver(manual_sync_remote_product, sender='magento2.MagentoProduct')
def sales_channels__magento__product__sync_from_remote(sender, instance, **kwargs):
    from .tasks import sync_magento_product_db_task
    from products.product_types import CONFIGURABLE
    product = instance.local_instance
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductFullSyncAddTask

    if product.type == CONFIGURABLE:
        number_of_remote_requests = 1 + product.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_runner = MagentoProductFullSyncAddTask(
        task_func=sync_magento_product_db_task,
        product=product,
        number_of_remote_requests=number_of_remote_requests,
        sales_channels_filter_kwargs={'id': instance.sales_channel.id},
    )
    task_runner.set_extra_task_kwargs(
        product_id=product.id,
        remote_product_id=instance.id,
    )
    task_runner.run()


@receiver(sales_view_assign_updated, sender='products.Product')
def sales_channels__magento__assign__update(sender, instance, **kwargs):
    from .tasks import update_magento_sales_view_assign_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoSingleChannelAddTask
    sales_channel = kwargs.get('sales_channel')

    task_runner = MagentoSingleChannelAddTask(
        task_func=update_magento_sales_view_assign_db_task,
        sales_channel=sales_channel,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def sales_channels__magento__product__create(sender, instance, **kwargs):
    from .tasks import create_magento_product_db_task
    from products.product_types import CONFIGURABLE
    from sales_channels.integrations.magento2.factories.task_queue import MagentoSingleChannelAddTask
    product = instance.product
    sales_channel = instance.sales_channel

    if not isinstance(sales_channel, MagentoSalesChannel):
        return

    if product.type == CONFIGURABLE:
        number_of_remote_requests = 1 + product.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_runner = MagentoSingleChannelAddTask(
        task_func=create_magento_product_db_task,
        sales_channel=sales_channel,
        number_of_remote_requests=number_of_remote_requests,
    )
    task_runner.set_extra_task_kwargs(product_id=product.id)
    task_runner.run()


@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def sales_channels__magento__product__delete_from_assign(sender, instance, **kwargs):
    from .tasks import delete_magento_product_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductDeleteFromAssignAddTask

    product = instance.product
    sales_channel = instance.sales_channel

    if not isinstance(sales_channel, MagentoSalesChannel):
        return

    task_runner = MagentoProductDeleteFromAssignAddTask(
        task_func=delete_magento_product_db_task,
        local_instance_id=product.id,
        sales_channel=sales_channel,
        is_variation=kwargs.get('is_variation', False),
    )
    task_runner.run()


@receiver(delete_remote_product, sender='products.Product')
def sales_channels__magento__product__delete_from_product(sender, instance, **kwargs):
    from .tasks import delete_magento_product_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoProductDeleteAddTask

    task_runner = MagentoProductDeleteAddTask(
        task_func=delete_magento_product_db_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        is_multiple=True,
    )
    task_runner.run()


@receiver(create_remote_vat_rate, sender='taxes.VatRate')
def sales_channels__magento__vat_rate__create(sender, instance, **kwargs):
    from .tasks import create_magento_vat_rate_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=create_magento_vat_rate_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(vat_rate_id=instance.id)
    task_runner.run()


@receiver(update_remote_vat_rate, sender='taxes.VatRate')
def sales_channels__magento__vat_rate__update(sender, instance, **kwargs):
    from .tasks import update_magento_vat_rate_db_task
    from sales_channels.integrations.magento2.factories.task_queue import MagentoChannelAddTask

    task_runner = MagentoChannelAddTask(
        task_func=update_magento_vat_rate_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(vat_rate_id=instance.id)
    task_runner.run()


@receiver(pre_delete, sender='taxes.VatRate')
def sales_channels__magento__vat_rate__delete(sender, instance, **kwargs):
    from sales_channels.integrations.magento2.models.taxes import MagentoTaxClass

    MagentoTaxClass.objects.filter(local_instance=instance).delete()
