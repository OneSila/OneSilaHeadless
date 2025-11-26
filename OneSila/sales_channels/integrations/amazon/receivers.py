import logging

from core.receivers import receiver
from core.signals import post_create, post_update
from django.db.models.signals import post_delete
from sales_channels.signals import (
    refresh_website_pull_models,
    sales_channel_created,
    manual_sync_remote_product,
    update_remote_product,
    create_remote_product,
    sales_view_assign_updated,
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
    delete_remote_image,
)
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
    AmazonProductBrowseNode,
    AmazonGtinExemption,
    AmazonProduct,
)
from sales_channels.integrations.amazon.factories.sync.rule_sync import (
    AmazonPropertyRuleItemSyncFactory,
)
from sales_channels.integrations.amazon.factories.sync.select_value_sync import (
    AmazonPropertySelectValuesSyncFactory,
)
from sales_channels.integrations.amazon.tasks import (
    create_amazon_product_type_rule_task,
    resync_amazon_product_db_task,
    amazon_translate_select_value_task,
    create_amazon_product_db_task,
)
from sales_channels.integrations.amazon.constants import (
    AMAZON_SELECT_VALUE_TRANSLATION_IGNORE_CODES,
)
from sales_channels.helpers import rebind_amazon_product_type_to_rule
from imports_exports.signals import import_success
from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonConfigurableVariationsFactory
from sales_channels.integrations.amazon.flows.tasks_runner import run_single_amazon_product_task_flow


logger = logging.getLogger(__name__)


def _log_amazon_product_signal(event_name, product, context=None):
    remote_product_ids = list(
        AmazonProduct.objects.filter(local_instance=product).values_list('id', flat=True)
    )
    sanitized_context = {}
    if context:
        sanitized_context = {key: value for key, value in context.items() if value is not None}

    logger.info(
        'Amazon receiver triggered: %s product_id=%s remote_product_ids=%s context=%s',
        event_name,
        getattr(product, 'id', None),
        remote_product_ids,
        sanitized_context,
    )


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='amazon.AmazonSalesChannel')
@receiver(sales_channel_created, sender='amazon.AmazonSalesChannel')
def sales_channels__amazon__handle_pull_views(sender, instance, **kwargs):
    from sales_channels.integrations.amazon.factories.sales_channels.views import (
        AmazonSalesChannelViewPullFactory,
    )
    from sales_channels.integrations.amazon.factories.sales_channels.languages import (
        AmazonRemoteLanguagePullFactory,
    )
    from sales_channels.integrations.amazon.factories.sales_channels.currencies import (
        AmazonRemoteCurrencyPullFactory,
    )

    if not isinstance(instance.get_real_instance(), AmazonSalesChannel):
        return
    if not instance.refresh_token:
        return

    views_factory = AmazonSalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = AmazonRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = AmazonRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()


@receiver(post_create, sender='amazon.AmazonProperty')
@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__sync_rule_item(sender, instance: AmazonProperty, **kwargs):
    """Sync ProductPropertiesRuleItem when an Amazon property is mapped locally."""
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return
    if signal == post_create and not instance.local_instance:
        return

    sync_factory = AmazonPropertyRuleItemSyncFactory(instance)
    sync_factory.run()


@receiver(post_create, sender='amazon.AmazonProperty')
@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__auto_map_select_values(sender, instance: AmazonProperty, **kwargs):
    """Automatically create local select values when duplicates exist across marketplaces."""
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return
    if signal == post_create and not instance.local_instance:
        return

    sync_factory = AmazonPropertySelectValuesSyncFactory(instance)
    sync_factory.run()


@receiver(post_update, sender='amazon.AmazonProperty')
def sales_channels__amazon_property__unmap_select_values(sender, instance: AmazonProperty, **kwargs):
    """Unmap select values when a property mapping changes."""
    if not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    AmazonPropertySelectValue.objects.filter(
        amazon_property=instance,
        local_instance__isnull=False,
    ).update(local_instance=None)


@receiver(post_create, sender='amazon.AmazonPropertySelectValue')
def sales_channels__amazon_property_select_value__translate(sender, instance: AmazonPropertySelectValue, **kwargs):
    """Translate remote select value names into the company language."""
    remote_language_obj = instance.marketplace.remote_languages.first()
    remote_lang = remote_language_obj.local_instance if remote_language_obj else None
    company_lang = instance.sales_channel.multi_tenant_company.language

    remote_name = instance.remote_name or instance.remote_value

    if instance.amazon_property.code in AMAZON_SELECT_VALUE_TRANSLATION_IGNORE_CODES:
        instance.translated_remote_name = remote_name
        instance.save(update_fields=['translated_remote_name'])
        return

    if not remote_lang or remote_lang == company_lang:
        instance.translated_remote_name = remote_name
        instance.save(update_fields=['translated_remote_name'])
        return

    amazon_translate_select_value_task(instance.id)


@receiver(post_update, sender='amazon.AmazonPropertySelectValue')
def sales_channels__amazon_property_select_value__auto_import(sender, instance: AmazonPropertySelectValue, **kwargs):
    """Auto-import mapped select values into product properties."""
    if not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    from sales_channels.integrations.amazon.tasks import amazon_auto_import_select_value_task

    amazon_auto_import_select_value_task(instance.id)


@receiver(post_update, sender="amazon.AmazonProductType")
def sales_channels__amazon_product_type__imported_rule(sender, instance, **kwargs):
    if instance.is_dirty_field("imported") and instance.imported:
        create_amazon_product_type_rule_task(
            product_type_code=instance.product_type_code,
            sales_channel_id=instance.sales_channel_id,
        )


@receiver(post_update, sender="amazon.AmazonProductType")
def sales_channels__amazon_product_type__ensure_specific_rule(sender, instance, **kwargs):
    if not instance.is_dirty_field(
        "local_instance",
        check_relationship=True,
    ):
        return

    if not instance.local_instance:
        return

    rebind_amazon_product_type_to_rule(
        product_type=instance,
        rule=instance.local_instance,
    )


@receiver(import_success, sender='amazon.AmazonSalesChannelImport')
def sales_channels__amazon_import_completed(sender, instance, **kwargs):

    if instance.type != instance.TYPE_PRODUCTS:
        return

    factory = AmazonConfigurableVariationsFactory(import_process=instance)
    factory.run()


@receiver(manual_sync_remote_product, sender='amazon.AmazonProduct')
def amazon__product__manual_sync(
    sender,
    instance,
    view,
    force_validation_only=False,
    force_full_update=False,
    **kwargs,
):
    """Queue a task to resync an Amazon product."""
    product = instance.local_instance
    count = 1 + (getattr(product, 'get_configurable_variations', lambda: [])().count())

    run_single_amazon_product_task_flow(
        task_func=resync_amazon_product_db_task,
        view=view,
        number_of_remote_requests=count,
        product_id=product.id,
        remote_product_id=instance.id,
        force_validation_only=force_validation_only,
        force_full_update=force_full_update,
    )


@receiver(post_update, sender="properties.ProductProperty")
@receiver(post_delete, sender="properties.ProductProperty")
def amazon__product_type_changed_clear_variation_theme(sender, instance, **kwargs):
    if not instance.property.is_product_type:
        return
    from sales_channels.integrations.amazon.models import AmazonVariationTheme

    AmazonVariationTheme.objects.filter(product=instance.product).delete()


@receiver(post_create, sender='amazon.AmazonProductBrowseNode')
@receiver(post_update, sender='amazon.AmazonProductBrowseNode')
def amazon__product_browse_node__propagate_to_variations(sender, instance, **kwargs):

    if not instance.product.is_configurable():
        return

    variations = instance.product.get_configurable_variations(active_only=False)
    for variation in variations:
        AmazonProductBrowseNode.objects.get_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            sales_channel=instance.sales_channel,
            view=instance.view,
            defaults={'recommended_browse_node_id': instance.recommended_browse_node_id},
        )


@receiver(post_create, sender='amazon.AmazonGtinExemption')
@receiver(post_update, sender='amazon.AmazonGtinExemption')
def amazon__gtin_exemption__propagate_to_variations(sender, instance, **kwargs):

    if not instance.product.is_configurable():
        return

    variations = instance.product.get_configurable_variations(active_only=False)
    for variation in variations:
        AmazonGtinExemption.objects.get_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            view=instance.view,
            defaults={'value': instance.value},
        )


@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def amazon__product__create_from_assign(sender, instance, view, **kwargs):
    sales_channel = instance.sales_channel.get_real_instance()

    if not isinstance(sales_channel, AmazonSalesChannel) or not sales_channel.active:
        return

    from django.conf import settings
    product = instance.product
    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    run_single_amazon_product_task_flow(
        task_func=create_amazon_product_db_task,
        view=view,
        number_of_remote_requests=count,
        product_id=product.id,
        force_validation_only=settings.DEBUG,
    )


@receiver(sales_view_assign_updated, sender='products.Product')
def amazon__assign__update(sender, instance, sales_channel, view, **kwargs):
    sales_channel = sales_channel.get_real_instance()
    is_delete = kwargs.get('is_delete', False)

    if not isinstance(sales_channel, AmazonSalesChannel) or not sales_channel.active or is_delete:
        return

    from django.conf import settings
    count = 1 + getattr(instance, 'get_configurable_variations', lambda: [])().count()

    run_single_amazon_product_task_flow(
        task_func=create_amazon_product_db_task,
        view=view,
        number_of_remote_requests=count,
        product_id=instance.id,
        force_validation_only=settings.DEBUG,
    )


@receiver(update_remote_product, sender='products.Product')
def amazon__product__update(sender, instance, **kwargs):
    _log_amazon_product_signal(
        'update_remote_product',
        instance,
        context={'payload_keys': sorted(kwargs.keys())},
    )


@receiver(create_remote_product_property, sender='properties.ProductProperty')
def amazon__product_property__create(sender, instance, **kwargs):
    product = instance.product
    property_obj = getattr(instance, 'property', None)
    _log_amazon_product_signal(
        'create_remote_product_property',
        product,
        context={
            'product_property_id': instance.id,
            'property_id': getattr(property_obj, 'id', None),
            'property_code': getattr(property_obj, 'code', None),
        },
    )


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def amazon__product_property__update(sender, instance, **kwargs):
    product = instance.product
    property_obj = getattr(instance, 'property', None)
    _log_amazon_product_signal(
        'update_remote_product_property',
        product,
        context={
            'product_property_id': instance.id,
            'property_id': getattr(property_obj, 'id', None),
            'property_code': getattr(property_obj, 'code', None),
            'payload_keys': sorted(kwargs.keys()),
        },
    )


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def amazon__product_property__delete(sender, instance, **kwargs):
    product = instance.product
    property_obj = getattr(instance, 'property', None)
    _log_amazon_product_signal(
        'delete_remote_product_property',
        product,
        context={
            'product_property_id': instance.id,
            'property_id': getattr(property_obj, 'id', None),
            'property_code': getattr(property_obj, 'code', None),
        },
    )


@receiver(update_remote_price, sender='products.Product')
def amazon__price__update(sender, instance, **kwargs):
    currency = kwargs.get('currency')
    _log_amazon_product_signal(
        'update_remote_price',
        instance,
        context={
            'currency_id': getattr(currency, 'id', None),
            'currency_code': getattr(currency, 'code', None),
            'currency_iso_code': getattr(currency, 'iso_code', None),
        },
    )


@receiver(update_remote_product_content, sender='products.Product')
def amazon__content__update(sender, instance, **kwargs):
    language = kwargs.get('language')
    _log_amazon_product_signal(
        'update_remote_product_content',
        instance,
        context={
            'language_id': getattr(language, 'id', None),
            'language_code': getattr(language, 'code', None),
            'language_iso_code': getattr(language, 'iso_code', None),
        },
    )


@receiver(update_remote_product_eancode, sender='products.Product')
def amazon__ean_code__update(sender, instance, **kwargs):
    _log_amazon_product_signal('update_remote_product_eancode', instance)


@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def amazon__variation__add(sender, parent_product, variation_product, **kwargs):
    _log_amazon_product_signal(
        'add_remote_product_variation',
        parent_product,
        context={
            'parent_product_id': getattr(parent_product, 'id', None),
            'variation_product_id': getattr(variation_product, 'id', None),
        },
    )


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def amazon__variation__remove(sender, parent_product, variation_product, **kwargs):
    _log_amazon_product_signal(
        'remove_remote_product_variation',
        parent_product,
        context={
            'parent_product_id': getattr(parent_product, 'id', None),
            'variation_product_id': getattr(variation_product, 'id', None),
        },
    )


@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def amazon__image_assoc__create(sender, instance, **kwargs):
    product = instance.product
    media = getattr(instance, 'media', None)
    _log_amazon_product_signal(
        'create_remote_image_association',
        product,
        context={
            'media_product_through_id': instance.id,
            'media_id': getattr(media, 'id', None),
            'media_type': getattr(media, 'type', None),
        },
    )


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def amazon__image_assoc__update(sender, instance, **kwargs):
    product = instance.product
    media = getattr(instance, 'media', None)
    _log_amazon_product_signal(
        'update_remote_image_association',
        product,
        context={
            'media_product_through_id': instance.id,
            'media_id': getattr(media, 'id', None),
            'media_type': getattr(media, 'type', None),
            'payload_keys': sorted(kwargs.keys()),
        },
    )


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def amazon__image_assoc__delete(sender, instance, **kwargs):
    product = instance.product
    media = getattr(instance, 'media', None)
    _log_amazon_product_signal(
        'delete_remote_image_association',
        product,
        context={
            'media_product_through_id': instance.id,
            'media_id': getattr(media, 'id', None),
            'media_type': getattr(media, 'type', None),
        },
    )


@receiver(delete_remote_image, sender='media.Media')
def amazon__image__delete(sender, instance, **kwargs):
    product_ids = list(instance.products.values_list('id', flat=True))
    remote_products = AmazonProduct.objects.filter(local_instance_id__in=product_ids)
    remote_map = {}
    for remote_product in remote_products:
        remote_map.setdefault(remote_product.local_instance_id, []).append(remote_product.id)

    logger.info(
        'Amazon receiver triggered: delete_remote_image image_id=%s product_ids=%s remote_product_ids=%s',
        instance.id,
        product_ids,
        remote_map,
    )
