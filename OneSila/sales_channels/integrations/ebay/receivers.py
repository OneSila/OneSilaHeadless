from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import (
    refresh_website_pull_models,
    sales_channel_created,
    manual_sync_remote_product,
    create_remote_product,
    sales_view_assign_updated,
)
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayProduct,
    EbayProductType,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.flows.internal_properties import (
    ensure_internal_properties_flow,
)
from sales_channels.integrations.ebay.factories.sync import (
    EbayPropertyRuleItemSyncFactory,
)
from sales_channels.integrations.ebay.tasks import (
    ebay_translate_property_task,
    ebay_translate_select_value_task,
    create_ebay_product_db_task,
    resync_ebay_product_db_task,
)
from sales_channels.integrations.ebay.flows.tasks_runner import run_single_ebay_product_task_flow

@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='ebay.EbaySalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='ebay.EbaySalesChannel')
def sales_channels__ebay__handle_pull(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.factories.sales_channels import (
        EbaySalesChannelViewPullFactory,
        EbayRemoteLanguagePullFactory,
        EbayRemoteCurrencyPullFactory,
    )

    if not isinstance(instance.get_real_instance(), EbaySalesChannel):
        return

    views_factory = EbaySalesChannelViewPullFactory(sales_channel=instance)
    views_factory.run()

    languages_factory = EbayRemoteLanguagePullFactory(sales_channel=instance)
    languages_factory.run()

    currencies_factory = EbayRemoteCurrencyPullFactory(sales_channel=instance)
    currencies_factory.run()

    ensure_internal_properties_flow(instance)


@receiver(post_create, sender='ebay.EbayProperty')
@receiver(post_update, sender='ebay.EbayProperty')
def sales_channels__ebay_property__sync_rule_item(sender, instance: EbayProperty, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('local_instance', check_relationship=True):
        return
    if signal == post_create and not instance.local_instance:
        return

    factory = EbayPropertyRuleItemSyncFactory(instance)
    factory.run()


@receiver(post_create, sender='ebay.EbayProductType')
@receiver(post_update, sender='ebay.EbayProductType')
def sales_channels__ebay_product_type__propagate_remote_id(sender, instance: EbayProductType, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('remote_id'):
        return
    if not instance.remote_id or not instance.local_instance_id:
        return

    from sales_channels.integrations.ebay.factories.sales_channels import (
        EbayProductTypeRemoteMappingFactory,
    )

    factory = EbayProductTypeRemoteMappingFactory(product_type=instance)
    factory.run()


@receiver(post_update, sender='ebay.EbayProperty')
def sales_channels__ebay_property__unmap_select_values(sender, instance: EbayProperty, **kwargs):
    if not instance.is_dirty_field('local_instance', check_relationship=True):
        return

    EbayPropertySelectValue.objects.filter(
        ebay_property=instance,
        local_instance__isnull=False,
    ).update(local_instance=None)


def _get_remote_language_code(view):
    if view is None:
        return None

    remote_language = view.remote_languages.first()
    return remote_language.local_instance if remote_language else None


@receiver(post_create, sender='ebay.EbayProperty')
@receiver(post_update, sender='ebay.EbayProperty')
def sales_channels__ebay_property__translate(sender, instance: EbayProperty, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field('localized_name'):
        return

    remote_lang = _get_remote_language_code(instance.marketplace)
    company_lang = instance.sales_channel.multi_tenant_company.language
    remote_name = instance.localized_name or instance.remote_id

    if not remote_name:
        return

    if not remote_lang or remote_lang == company_lang:
        if instance.translated_name != remote_name:
            instance.translated_name = remote_name
            instance.save(update_fields=['translated_name'])
        return

    ebay_translate_property_task(instance.id)


@receiver(post_create, sender='ebay.EbayPropertySelectValue')
def sales_channels__ebay_property_select_value__translate(sender, instance: EbayPropertySelectValue, **kwargs):
    remote_lang = _get_remote_language_code(instance.marketplace)
    company_lang = instance.sales_channel.multi_tenant_company.language
    remote_name = instance.localized_value or instance.remote_id

    if not remote_name:
        return

    if not remote_lang or remote_lang == company_lang:
        if instance.translated_value != remote_name:
            instance.translated_value = remote_name
            instance.save(update_fields=['translated_value'])
        return

    ebay_translate_select_value_task(instance.id)


@receiver(manual_sync_remote_product, sender='ebay.EbayProduct')
def ebay__product__manual_sync(
    sender,
    instance: EbayProduct,
    view=None,
    force_validation_only: bool = False,
    force_full_update: bool = False,
    **kwargs,
):
    product = instance.local_instance
    if product is None:
        return

    if view is None:
        return

    resolved_view = view.get_real_instance()
    sales_channel = resolved_view.sales_channel.get_real_instance()

    if not isinstance(sales_channel, EbaySalesChannel) or not sales_channel.active:
        return

    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    run_single_ebay_product_task_flow(
        task_func=resync_ebay_product_db_task,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=product.id,
        remote_product_id=instance.id,
    )


@receiver(create_remote_product, sender='sales_channels.SalesChannelViewAssign')
def ebay__product__create_from_assign(sender, instance, view, **kwargs):
    sales_channel = instance.sales_channel.get_real_instance()

    if not isinstance(sales_channel, EbaySalesChannel) or not sales_channel.active:
        return

    resolved_view = view.get_real_instance()
    product = instance.product
    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    run_single_ebay_product_task_flow(
        task_func=create_ebay_product_db_task,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=product.id,
    )


@receiver(sales_view_assign_updated, sender='products.Product')
def ebay__assign__update(sender, instance, sales_channel, view, **kwargs):
    sales_channel = sales_channel.get_real_instance()
    is_delete = kwargs.get('is_delete', False)

    if not isinstance(sales_channel, EbaySalesChannel) or not sales_channel.active or is_delete:
        return

    resolved_view = view.get_real_instance()
    count = 1 + getattr(instance, 'get_configurable_variations', lambda: [])().count()

    run_single_ebay_product_task_flow(
        task_func=create_ebay_product_db_task,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=instance.id,
    )
