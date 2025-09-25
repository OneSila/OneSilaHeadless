from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import refresh_website_pull_models, sales_channel_created
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
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
)

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
