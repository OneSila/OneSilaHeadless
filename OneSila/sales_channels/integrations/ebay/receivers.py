from collections import Counter

from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.signals import (
    refresh_website_pull_models,
    sales_channel_created,
    manual_sync_remote_product,
    create_remote_product,
    delete_remote_product,
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
    ebay_product_type_rule_sync_task,
    create_ebay_product_db_task,
    resync_ebay_product_db_task,
    update_ebay_assign_offers_db_task,
    delete_ebay_assign_offers_db_task,
    delete_ebay_product_db_task,
)
from sales_channels.integrations.ebay.flows.tasks_runner import run_single_ebay_product_task_flow
from sales_channels.models import SalesChannelViewAssign
from sales_channels.helpers import rebind_ebay_product_type_to_rule


_PENDING_PRODUCT_DELETE_COUNTS: Counter[int] = Counter()


def _get_remote_request_count(product) -> int:
    getter = getattr(product, 'get_configurable_variations', None)
    if callable(getter):
        try:
            return 1 + getter().count()
        except Exception:  # pragma: no cover - defensive
            return 1
    return 1


def _queue_delete_product_task(*, product, sales_channel, view) -> bool:
    if product is None or view is None:
        return False

    remote_exists = EbayProduct.objects.filter(
        sales_channel=sales_channel,
        local_instance=product,
    ).exists()

    if not remote_exists:
        return False

    remote_requests = _get_remote_request_count(product)
    run_single_ebay_product_task_flow(
        task_func=delete_ebay_product_db_task,
        view=view,
        number_of_remote_requests=remote_requests,
        product_id=product.id,
    )
    return True

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


@receiver(post_create, sender='ebay.EbayProductType')
@receiver(post_update, sender='ebay.EbayProductType')
def sales_channels__ebay_product_type__ensure_specific_rule(sender, instance: EbayProductType, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not instance.is_dirty_field(
        'local_instance',
        check_relationship=True,
    ):
        return

    if not instance.local_instance:
        return

    rebind_ebay_product_type_to_rule(
        product_type=instance,
        rule=instance.local_instance,
    )


@receiver(post_update, sender='ebay.EbayProductType')
def sales_channels__ebay_product_type__sync_rule(sender, instance: EbayProductType, **kwargs):
    signal = kwargs.get('signal')
    if signal == post_update and not (
        instance.is_dirty_field('remote_id')
        or instance.is_dirty_field('local_instance', check_relationship=True)
    ):
        return

    remote_id = (instance.remote_id or '').strip()
    if not remote_id or not instance.local_instance_id or not instance.marketplace_id:
        return

    ebay_product_type_rule_sync_task(product_type_id=instance.id)


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
    if view is None:
        return

    resolved_channel = sales_channel.get_real_instance()
    if not isinstance(resolved_channel, EbaySalesChannel) or not resolved_channel.active:
        return

    resolved_view = view.get_real_instance()
    if resolved_view is None:
        return

    count = 1 + getattr(instance, 'get_configurable_variations', lambda: [])().count()
    is_delete = kwargs.get('is_delete', False)
    task_func = delete_ebay_assign_offers_db_task if is_delete else update_ebay_assign_offers_db_task

    run_single_ebay_product_task_flow(
        task_func=task_func,
        view=resolved_view,
        number_of_remote_requests=count,
        product_id=instance.id,
    )


@receiver(delete_remote_product, sender='sales_channels.SalesChannelViewAssign')
def ebay__assign__delete(sender, instance, is_variation=False, **kwargs):
    product = getattr(instance, 'product', None)
    product_id = getattr(product, 'id', None)
    if product is None or product_id is None:
        return

    pending = _PENDING_PRODUCT_DELETE_COUNTS.get(product_id, 0)
    if pending:
        remaining = pending - 1
        if remaining > 0:
            _PENDING_PRODUCT_DELETE_COUNTS[product_id] = remaining
        else:
            _PENDING_PRODUCT_DELETE_COUNTS.pop(product_id, None)
        return

    sales_channel = instance.sales_channel.get_real_instance()
    if not isinstance(sales_channel, EbaySalesChannel) or not sales_channel.active:
        return

    resolved_view = instance.sales_channel_view.get_real_instance()
    if resolved_view is None:
        return

    _queue_delete_product_task(
        product=product,
        sales_channel=sales_channel,
        view=resolved_view,
    )


@receiver(delete_remote_product, sender='products.Product')
def ebay__product__delete(sender, instance, **kwargs):
    product = instance
    product_id = getattr(product, 'id', None)
    if product_id is None:
        return

    assignments = (
        SalesChannelViewAssign.objects.filter(product=product)
        .select_related('sales_channel', 'sales_channel_view')
    )

    scheduled = 0
    for assign in assignments:
        sales_channel = assign.sales_channel.get_real_instance()
        if not isinstance(sales_channel, EbaySalesChannel) or not sales_channel.active:
            continue

        resolved_view = assign.sales_channel_view.get_real_instance()
        if resolved_view is None:
            continue

        if _queue_delete_product_task(
            product=product,
            sales_channel=sales_channel,
            view=resolved_view,
        ):
            scheduled += 1

    if scheduled:
        _PENDING_PRODUCT_DELETE_COUNTS[product_id] += scheduled


@receiver(post_create, sender='ebay.EbayProductCategory')
@receiver(post_update, sender='ebay.EbayProductCategory')
def ebay__product_category__propagate_to_variations(sender, instance, **kwargs):
    """
    When an eBay category is assigned to a configurable (parent) product,
    automatically propagate it to all its variations.
    """
    from sales_channels.integrations.ebay.models.categories import EbayProductCategory

    if not instance.product.is_configurable():
        return

    variations = instance.product.get_configurable_variations(active_only=False)
    for variation in variations:
        EbayProductCategory.objects.get_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            sales_channel=instance.sales_channel,
            view=instance.view,
            defaults={'remote_id': instance.remote_id},
        )
