from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.signals import post_update, mutation_update
from sales_channels.integrations.shopify.constants import SHOPIFY_TAGS
from sales_channels.integrations.shopify.tasks import create_shopify_product_db_task, \
    create_shopify_product_property_db_task, update_shopify_product_property_db_task, \
    delete_shopify_product_property_db_task, update_shopify_price_db_task, update_shopify_product_content_db_task, \
    update_shopify_product_eancode_db_task, add_shopify_product_variation_db_task, \
    remove_shopify_product_variation_db_task, create_shopify_image_association_db_task, \
    update_shopify_image_association_db_task, delete_shopify_image_association_db_task, delete_shopify_image_db_task, \
    update_shopify_product_db_task, sync_shopify_product_db_task, delete_shopify_product_db_task
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
    delete_remote_image, refresh_website_pull_models,
)

from sales_channels.integrations.shopify.models import ShopifySalesChannel


#
# 1) Product create (on assign)
#
@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def shopify__product__create_from_assign(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifySingleChannelAddTask

    product = instance.product
    sc = instance.sales_channel.get_real_instance()

    if not isinstance(sc, ShopifySalesChannel):
        return

    task_runner = ShopifySingleChannelAddTask(
        task_func=create_shopify_product_db_task,
        sales_channel=sc,
        number_of_remote_requests=1,
    )
    task_runner.set_extra_task_kwargs(product_id=product.id)
    task_runner.run()


#
# 2) Product update
#
@receiver(update_remote_product, sender='products.Product')
def shopify__product__update(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductUpdateAddTask

    task_runner = ShopifyProductUpdateAddTask(
        task_func=update_shopify_product_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


#
# 3) Product delete (from view‐assign removal)
#
@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def shopify__product__delete_from_assign(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductDeleteFromAssignAddTask

    product = instance.product
    sales_channel = instance.sales_channel.get_real_instance()

    if not isinstance(sales_channel, ShopifySalesChannel):
        return

    task_runner = ShopifyProductDeleteFromAssignAddTask(
        task_func=delete_shopify_product_db_task,
        local_instance_id=product.id,
        sales_channel=sales_channel,
        is_variation=kwargs.get('is_variation', False),
    )
    task_runner.run()


#
# 4) Product delete (from product deletion)
#
@receiver(delete_remote_product, sender='products.Product')
def shopify__product__delete_from_product(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductDeleteAddTask

    task_runner = ShopifyProductDeleteAddTask(
        task_func=delete_shopify_product_db_task,
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
def shopify__product__sync_from_local(sender, instance, **kwargs):
    # number of calls = 1 + variations
    count = 1 + (instance.get_configurable_variations().count()
                 if hasattr(instance, 'get_configurable_variations') else 0)
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductFullSyncAddTask

    task_runner = ShopifyProductFullSyncAddTask(
        task_func=sync_shopify_product_db_task,
        product=instance,
        number_of_remote_requests=count,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(sync_remote_product, sender='shopify.ShopifyProduct')
@receiver(manual_sync_remote_product, sender='shopify.ShopifyProduct')
def shopify__product__sync_from_remote(sender, instance, **kwargs):
    product = instance.local_instance
    count = 1 + (getattr(product, 'get_configurable_variations', lambda: [])().count())
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyRemoteProductFullSyncAddTask

    task_runner = ShopifyRemoteProductFullSyncAddTask(
        task_func=sync_shopify_product_db_task,
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
def shopify__product_property__create(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductPropertyAddTask

    task_runner = ShopifyProductPropertyAddTask(
        task_func=create_shopify_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(product_property_id=instance.id)
    task_runner.run()


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def shopify__product_property__update(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductPropertyAddTask

    task_runner = ShopifyProductPropertyAddTask(
        task_func=update_shopify_product_property_db_task,
        product=instance.product,
    )
    task_runner.set_extra_task_kwargs(product_property_id=instance.id)
    task_runner.run()


@receiver(post_update, sender='properties.ProductProperty')
@receiver(mutation_update, sender='properties.ProductProperty')
@receiver(post_delete, sender='properties.ProductProperty')
def shopify__product_property__tags__update(sender, instance, **kwargs):
    product = instance.product

    if instance.property.internal_name == SHOPIFY_TAGS:
        from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductFullSyncAddTask

        task_runner = ShopifyProductFullSyncAddTask(
            task_func=sync_shopify_product_db_task,
            product=product,
        )
        task_runner.set_extra_task_kwargs(product_id=product.id)
        task_runner.run()


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def shopify__product_property__delete(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductPropertyDeleteAddTask

    task_runner = ShopifyProductPropertyDeleteAddTask(
        task_func=delete_shopify_product_property_db_task,
        product=instance.product,
        local_instance_id=instance.id,
    )
    task_runner.run()


#
# 7) Price update
#
@receiver(update_remote_price, sender='products.Product')
def shopify__price__update(sender, instance, **kwargs):
    currency = kwargs.get('currency')

    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductPriceAddTask

    task_runner = ShopifyProductPriceAddTask(
        task_func=update_shopify_price_db_task,
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
def shopify__content__update(sender, instance, **kwargs):
    language = kwargs.get('language', None)

    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductContentAddTask

    task_runner = ShopifyProductContentAddTask(
        task_func=update_shopify_product_content_db_task,
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
def shopify__ean_code__update(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductEanCodeAddTask

    task_runner = ShopifyProductEanCodeAddTask(
        task_func=update_shopify_product_eancode_db_task,
        product=instance,
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


#
# 10) Add / Remove variation
#
@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def shopify__variation__add(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyChannelAddTask

    task_runner = ShopifyChannelAddTask(
        task_func=add_shopify_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )
    task_runner.run()


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def shopify__variation__remove(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyChannelAddTask

    task_runner = ShopifyChannelAddTask(
        task_func=remove_shopify_product_variation_db_task,
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
def shopify__image_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductImagesAddTask

    task_runner = ShopifyProductImagesAddTask(
        task_func=create_shopify_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def shopify__image_assoc__update(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyProductImagesAddTask

    task_runner = ShopifyProductImagesAddTask(
        task_func=update_shopify_image_association_db_task,
        product=instance.product,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.set_extra_task_kwargs(media_product_through_id=instance.id)
    task_runner.run()


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def shopify__image_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyImageAssociationDeleteAddTask

    task_runner = ShopifyImageAssociationDeleteAddTask(
        task_func=delete_shopify_image_association_db_task,
        product=instance.product,
        local_instance_id=instance.id,
        sales_channels_filter_kwargs={'id': instance.sales_channel_id} if instance.sales_channel_id else None,
    )
    task_runner.run()


#
# 12) Image delete
#
@receiver(delete_remote_image, sender='media.Media')
def shopify__image__delete(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.task_queue import ShopifyChannelAddTask

    task_runner = ShopifyChannelAddTask(
        task_func=delete_shopify_image_db_task,
        multi_tenant_company=instance.multi_tenant_company,
    )
    task_runner.set_extra_task_kwargs(image_id=instance.id)
    task_runner.run()


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='shopify.ShopifySalesChannel')
def sales_channels__shopify__handle_pull_magento_sales_channel_views(sender, instance, **kwargs):
    from sales_channels.integrations.shopify.factories.sales_channels.views import ShopifySalesChannelViewPullFactory
    from sales_channels.integrations.shopify.factories.sales_channels.languages import ShopifyRemoteLanguagePullFactory
    from sales_channels.integrations.shopify.factories.sales_channels.currencies import ShopifyRemoteCurrencyPullFactory

    if not isinstance(instance.get_real_instance(), ShopifySalesChannel):
        return

    if instance.access_token is None:
        return

    views_factory = ShopifySalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = ShopifyRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = ShopifyRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()
