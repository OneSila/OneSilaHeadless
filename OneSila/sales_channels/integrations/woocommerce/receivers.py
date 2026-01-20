from django.dispatch import receiver
from sales_channels.integrations.woocommerce.tasks import create_woocommerce_product_db_task, \
    create_woocommerce_product_property_db_task, update_woocommerce_product_property_db_task, \
    delete_woocommerce_product_property_db_task, update_woocommerce_price_db_task, update_woocommerce_product_content_db_task, \
    update_woocommerce_product_eancode_db_task, add_woocommerce_product_variation_db_task, \
    remove_woocommerce_product_variation_db_task, create_woocommerce_image_association_db_task, \
    update_woocommerce_image_association_db_task, delete_woocommerce_image_association_db_task, delete_woocommerce_image_db_task, \
    update_woocommerce_product_db_task, sync_woocommerce_product_db_task, delete_woocommerce_product_db_task
from sales_channels.signals import (
    create_remote_product,
    delete_remote_product,
    update_remote_product,
    sync_remote_product,
    manual_sync_remote_product,
    create_remote_product_property,
    update_remote_product_property,
    delete_remote_product_property,
    update_remote_price,
    update_remote_product_content,
    update_remote_product_eancode,
    add_remote_product_variation,
    remove_remote_product_variation,
    create_remote_image_association,
    update_remote_image_association,
    delete_remote_image_association,
    delete_remote_image, refresh_website_pull_models, sales_channel_created,
)

from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel

import logging
logger = logging.getLogger(__name__)


#
# 1) Product create (on assign)
#
@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def woocommerce__product__create_from_assign(sender, instance, **kwargs):
    from products.product_types import CONFIGURABLE
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceSingleChannelAddTask

    product = instance.product
    sales_channel = instance.sales_channel

    if not isinstance(sales_channel, WoocommerceSalesChannel):
        return

    if product.type == CONFIGURABLE:
        number_of_remote_requests = 1 + product.get_configurable_variations().count()
    else:
        number_of_remote_requests = 1

    task_runner = WooCommerceSingleChannelAddTask(
        task_func=create_woocommerce_product_db_task,
        sales_channel=sales_channel,
        number_of_remote_requests=number_of_remote_requests,
    )
    task_runner.set_extra_task_kwargs(product_id=product.id)
    task_runner.run()


#
# 2) Product update
#
@receiver(update_remote_product, sender='products.Product')
def woocommerce__product__update(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductUpdateAddTask

    task_runner = WooCommerceProductUpdateAddTask(
        task_func=update_woocommerce_product_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


#
# 3) Product delete (from view‐assign removal)
#
@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def woocommerce__product__delete_from_assign(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductDeleteFromAssignAddTask

    product = instance.product
    sales_channel = instance.sales_channel

    task_runner = WooCommerceProductDeleteFromAssignAddTask(
        task_func=delete_woocommerce_product_db_task,
        local_instance_id=product.id,
        sales_channel=sales_channel,
        is_variation=kwargs.get('is_variation', False),
    )
    task_runner.run()


#
# 4) Product delete (from product deletion)
#
@receiver(delete_remote_product, sender='products.Product')
def woocommerce__product__delete_from_product(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductDeleteAddTask

    task_runner = WooCommerceProductDeleteAddTask(
        task_func=delete_woocommerce_product_db_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        is_multiple=True,
    )
    task_runner.run()


#
# 5) Sync product
#
@receiver(sync_remote_product, sender='products.Product')
@receiver(manual_sync_remote_product, sender='products.Product')
def woocommerce__product__sync_from_local(sender, instance, **kwargs):
    # number of calls = 1 + variations
    count = 1 + (instance.get_configurable_variations().count()
                 if hasattr(instance, 'get_configurable_variations') else 0)
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductFullSyncAddTask

    task_runner = WooCommerceProductFullSyncAddTask(
        task_func=sync_woocommerce_product_db_task,
        product=instance,
        number_of_remote_requests=count,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(sync_remote_product, sender='woocommerce.WoocommerceProduct')
@receiver(manual_sync_remote_product, sender='woocommerce.WoocommerceProduct')
def woocommerce__product__sync_from_remote(sender, instance, **kwargs):
    product = instance.local_instance
    count = 1 + (getattr(product, 'get_configurable_variations', lambda: [])().count())
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceRemoteProductFullSyncAddTask

    task_runner = WooCommerceRemoteProductFullSyncAddTask(
        task_func=sync_woocommerce_product_db_task,
        product=product,
        sales_channel=instance.sales_channel,
        number_of_remote_requests=count,
    )
    task_runner.set_extra_task_kwargs(product_id=product.id)
    task_runner.run()


#
# 6) Product property create/update/delete
#
@receiver(create_remote_product_property, sender='properties.ProductProperty')
def woocommerce__product_property__create(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductPropertyAddTask

    task_runner = WooCommerceProductPropertyAddTask(
        task_func=create_woocommerce_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(product_property_id=instance.id)
    task_runner.run()


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def woocommerce__product_property__update(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductPropertyAddTask

    task_runner = WooCommerceProductPropertyAddTask(
        task_func=update_woocommerce_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(product_property_id=instance.id)
    task_runner.run()


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def woocommerce__product_property__delete(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductPropertyDeleteAddTask

    task_runner = WooCommerceProductPropertyDeleteAddTask(
        task_func=delete_woocommerce_product_property_db_task,
        product=instance.product,
        local_instance_id=instance.id,
    )
    task_runner.run()


#
# 7) Price update
#
@receiver(update_remote_price, sender='products.Product')
def woocommerce__price__update(sender, instance, **kwargs):
    currency = kwargs.get('currency')

    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductPriceAddTask

    task_runner = WooCommerceProductPriceAddTask(
        task_func=update_woocommerce_price_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(
        product_id=instance.id,
        currency_id=currency.id,
    )
    task_runner.run()


#
# 8) Content update
#
@receiver(update_remote_product_content, sender='products.Product')
def woocommerce__content__update(sender, instance, **kwargs):
    language = kwargs.get('language', None)

    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductContentAddTask

    task_runner = WooCommerceProductContentAddTask(
        task_func=update_woocommerce_product_content_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(
        product_id=instance.id,
        language=language,
    )
    task_runner.run()


#
# 9) EAN code update
#
@receiver(update_remote_product_eancode, sender='products.Product')
def woocommerce__ean_code__update(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductEanCodeAddTask

    task_runner = WooCommerceProductEanCodeAddTask(
        task_func=update_woocommerce_product_eancode_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


#
# 10) Add / Remove variation
#
@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def woocommerce__variation__add(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceChannelAddTask

    task_runner = WooCommerceChannelAddTask(
        task_func=add_woocommerce_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )
    task_runner.run()


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def woocommerce__variation__remove(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceChannelAddTask

    task_runner = WooCommerceChannelAddTask(
        task_func=remove_woocommerce_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )
    task_runner.run()


#
# 11) Image associations
#
@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def woocommerce__image_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductImagesAddTask

    task_runner = WooCommerceProductImagesAddTask(
        task_func=create_woocommerce_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def woocommerce__image_assoc__update(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceProductImagesAddTask

    task_runner = WooCommerceProductImagesAddTask(
        task_func=update_woocommerce_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def woocommerce__image_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceImageAssociationDeleteAddTask

    task_runner = WooCommerceImageAssociationDeleteAddTask(
        task_func=delete_woocommerce_image_association_db_task,
        product=instance.product,
        local_instance_id=instance.id,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.run()


#
# 12) Image delete
#
@receiver(delete_remote_image, sender='media.Media')
def woocommerce__image__delete(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.task_queue import WooCommerceChannelAddTask

    task_runner = WooCommerceChannelAddTask(
        task_func=delete_woocommerce_image_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(image_id=instance.id)
    task_runner.run()


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='woocommerce.WoocommerceSalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='woocommerce.WoocommerceSalesChannel')
def sales_channels__woocommerce__handle_pull_woocommerce_sales_channel_views(sender, instance, **kwargs):
    from sales_channels.integrations.woocommerce.factories.pulling import (
        WoocommerceSalesChannelViewPullFactory,
        WoocommerceRemoteCurrencyPullFactory,
        WoocommerceLanguagePullFactory
    )

    views_factory = WoocommerceSalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = WoocommerceLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = WoocommerceRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()
