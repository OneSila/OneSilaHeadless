from django.dispatch import receiver
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

from sales_channels.flows.default import (
    run_generic_sales_channel_task_flow,
    run_product_specific_sales_channel_task_flow,
    run_delete_product_specific_generic_sales_channel_task_flow, run_delete_generic_sales_channel_task_flow,
)

from sales_channels.integrations.shopify.models import ShopifySalesChannel, ShopifyProductProperty, \
    ShopifyImageProductAssociation, ShopifyProduct


#
# 1) Product create (on assign)
#
@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def shopify__product__create_from_assign(sender, instance, **kwargs):

    product = instance.product
    sc = instance.sales_channel.get_real_instance()

    if not isinstance(sc, ShopifySalesChannel):
        return

    # from sales_channels.integrations.shopify.factories.products.products import  ShopifyProductCreateFactory
    #
    # product = instance.product
    # sc = instance.sales_channel
    #
    # fac = ShopifyProductCreateFactory(sales_channel=sc, local_instance=product)
    # fac.run()

    run_generic_sales_channel_task_flow(
        task_func=create_shopify_product_db_task,
        multi_tenant_company=product.multi_tenant_company,
        sales_channels_filter_kwargs={'id': sc.id},
        number_of_remote_requests=1,
        sales_channel_class=ShopifySalesChannel,
        product_id=product.id,
    )


#
# 2) Product update
#
@receiver(update_remote_product, sender='products.Product')
def shopify__product__update(sender, instance, **kwargs):
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        sales_channel_class=ShopifySalesChannel,
        product_id=instance.id,
    )


#
# 3) Product delete (from view‐assign removal)
#
@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def shopify__product__delete_from_assign(sender, instance, **kwargs):

    product = instance.product
    sales_channel = instance.sales_channel.get_real_instance()

    if not isinstance(sales_channel, ShopifySalesChannel):
        return

    run_delete_generic_sales_channel_task_flow(
        task_func=delete_shopify_product_db_task,
        local_instance_id=product.id,
        remote_class=ShopifyProduct,
        multi_tenant_company=product.multi_tenant_company,
        sales_channels_filter_kwargs={'id': sales_channel.id},
        is_variation=kwargs.get('is_variation', False),
        sales_channel_class=ShopifySalesChannel
    )


#
# 4) Product delete (from product deletion)
#
@receiver(delete_remote_product, sender='products.Product')
def shopify__product__delete_from_product(sender, instance, **kwargs):

    run_delete_generic_sales_channel_task_flow(
        task_func=delete_shopify_product_db_task,
        local_instance_id=instance.id,
        remote_class=ShopifyProduct,
        multi_tenant_company=instance.multi_tenant_company,
        is_multiple=True,
        sales_channel_class=ShopifySalesChannel,
    )


#
# 5) Sync product
#
@receiver(sync_remote_product, sender='products.Product')
def shopify__product__sync_from_local(sender, instance, **kwargs):
    # number of calls = 1 + variations
    count = 1 + (instance.get_configurable_variations().count()
                 if hasattr(instance, 'get_configurable_variations') else 0)
    run_product_specific_sales_channel_task_flow(
        task_func=sync_shopify_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=count,
        sales_channel_class=ShopifySalesChannel,
        product_id=instance.id,
    )


@receiver(sync_remote_product, sender='shopify.ShopifyProduct')
def shopify__product__sync_from_remote(sender, instance, **kwargs):
    product = instance.local_instance
    count = 1 + (getattr(product, 'get_configurable_variations', lambda: [])().count())
    run_generic_sales_channel_task_flow(
        task_func=sync_shopify_product_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        sales_channels_filter_kwargs={'id': instance.sales_channel.id},
        number_of_remote_requests=count,
        sales_channel_class=ShopifySalesChannel,
        product_id=product.id,
        remote_product_id=instance.id,
    )


#
# 6) Product property create/update/delete
#
@receiver(create_remote_product_property, sender='properties.ProductProperty')
def shopify__product_property__create(sender, instance, **kwargs):
    run_product_specific_sales_channel_task_flow(
        task_func=create_shopify_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
        product_property_id=instance.id,
    )


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def shopify__product_property__update(sender, instance, **kwargs):
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
        product_property_id=instance.id,
    )


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def shopify__product_property__delete(sender, instance, **kwargs):
    run_delete_product_specific_generic_sales_channel_task_flow(
        task_func=delete_shopify_product_property_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=ShopifyProductProperty,
        local_instance_id=instance.id,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
    )


#
# 7) Price update
#
@receiver(update_remote_price, sender='products.Product')
def shopify__price__update(sender, instance, **kwargs):
    currency = kwargs.get('currency')

    task_kwargs = {'product_id': instance.id, 'currency_id': currency.id}
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_price_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        sales_channel_class=ShopifySalesChannel,
        **task_kwargs
    )


#
# 8) Content update
#
@receiver(update_remote_product_content, sender='products.Product')
def shopify__content__update(sender, instance, **kwargs):
    language = kwargs.get('language', None)

    task_kwargs = {'product_id': instance.id, 'language': language}
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_product_content_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        sales_channel_class=ShopifySalesChannel,
        **task_kwargs
    )


#
# 9) EAN code update
#
@receiver(update_remote_product_eancode, sender='products.Product')
def shopify__ean_code__update(sender, instance, **kwargs):

    task_kwargs = {'product_id': instance.id}
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_product_eancode_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        sales_channel_class=ShopifySalesChannel,
        **task_kwargs
    )


#
# 10) Add / Remove variation
#
@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def shopify__variation__add(sender, parent_product, variation_product, **kwargs):
    run_generic_sales_channel_task_flow(
        task_func=add_shopify_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
        sales_channel_class=ShopifySalesChannel,
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def shopify__variation__remove(sender, parent_product, variation_product, **kwargs):
    run_generic_sales_channel_task_flow(
        task_func=remove_shopify_product_variation_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
        sales_channel_class=ShopifySalesChannel,
        parent_product_id=parent_product.id,
        variation_product_id=variation_product.id,
    )


#
# 11) Image associations
#
@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def shopify__image_assoc__create(sender, instance, **kwargs):
    run_product_specific_sales_channel_task_flow(
        task_func=create_shopify_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
        media_product_through_id=instance.id,
    )


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def shopify__image_assoc__update(sender, instance, **kwargs):
    run_product_specific_sales_channel_task_flow(
        task_func=update_shopify_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
        media_product_through_id=instance.id,
    )


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def shopify__image_assoc__delete(sender, instance, **kwargs):
    run_delete_product_specific_generic_sales_channel_task_flow(
        task_func=delete_shopify_image_association_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        remote_class=ShopifyImageProductAssociation,
        local_instance_id=instance.id,
        product=instance.product,
        sales_channel_class=ShopifySalesChannel,
    )


#
# 12) Image delete
#
@receiver(delete_remote_image, sender='media.Media')
def shopify__image__delete(sender, instance, **kwargs):
    run_generic_sales_channel_task_flow(
        task_func=delete_shopify_image_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        sales_channel_class=ShopifySalesChannel,
        image_id=instance.id,
    )


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
