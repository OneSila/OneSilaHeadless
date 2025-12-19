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
    update_remote_product,
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
from sales_channels.integrations.ebay.flows.tasks_runner import (
    run_product_ebay_sales_channel_task_flow,
    run_single_ebay_product_task_flow,
)
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


@receiver(update_remote_product, sender='products.Product')
def ebay__product__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__product__update_db_task,
    )

    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__product__update_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=0,
        context={"payload_keys": sorted(kwargs.keys())},
    )


@receiver(create_remote_product_property, sender='properties.ProductProperty')
def ebay__product_property__create(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__product_property__create_db_task,
    )

    product = instance.product
    property_obj = getattr(instance, "property", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__product_property__create_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
        },
    )


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def ebay__product_property__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__product_property__update_db_task,
    )

    product = instance.product
    property_obj = getattr(instance, "property", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__product_property__update_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
            "payload_keys": sorted(kwargs.keys()),
        },
    )


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def ebay__product_property__delete(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__product_property__delete_db_task,
    )

    product = instance.product
    property_obj = getattr(instance, "property", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__product_property__delete_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
        },
    )


@receiver(update_remote_price, sender='products.Product')
def ebay__price__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__price__update_db_task,
    )

    currency = kwargs.get("currency")
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__price__update_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=0,
        context={
            "currency_id": getattr(currency, "id", None),
            "currency_code": getattr(currency, "code", None),
            "currency_iso_code": getattr(currency, "iso_code", None),
        },
    )


@receiver(update_remote_product_content, sender='products.Product')
def ebay__content__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__content__update_db_task,
    )

    language = kwargs.get("language")
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__content__update_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=0,
        context={
            "language_id": getattr(language, "id", None),
            "language_code": getattr(language, "code", None),
            "language_iso_code": getattr(language, "iso_code", None),
        },
    )


@receiver(update_remote_product_eancode, sender='products.Product')
def ebay__ean_code__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__ean_code__update_db_task,
    )

    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__ean_code__update_db_task,
        multi_tenant_company=instance.multi_tenant_company,
        product=instance,
        number_of_remote_requests=0,
        context=None,
    )


@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def ebay__variation__add(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__variation__add_db_task,
    )

    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__variation__add_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
        product=parent_product,
        number_of_remote_requests=0,
        context={
            "parent_product_id": getattr(parent_product, "id", None),
            "variation_product_id": getattr(variation_product, "id", None),
        },
    )


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def ebay__variation__remove(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__variation__remove_db_task,
    )

    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__variation__remove_db_task,
        multi_tenant_company=parent_product.multi_tenant_company,
        product=parent_product,
        number_of_remote_requests=0,
        context={
            "parent_product_id": getattr(parent_product, "id", None),
            "variation_product_id": getattr(variation_product, "id", None),
        },
    )


@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def ebay__image_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__image_assoc__create_db_task,
    )

    product = instance.product
    media = getattr(instance, "media", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__image_assoc__create_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
        },
    )


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def ebay__image_assoc__update(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__image_assoc__update_db_task,
    )

    product = instance.product
    media = getattr(instance, "media", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__image_assoc__update_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
            "payload_keys": sorted(kwargs.keys()),
        },
    )


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def ebay__image_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__image_assoc__delete_db_task,
    )

    product = instance.product
    media = getattr(instance, "media", None)
    run_product_ebay_sales_channel_task_flow(
        task_func=ebay__image_assoc__delete_db_task,
        multi_tenant_company=product.multi_tenant_company,
        product=product,
        number_of_remote_requests=0,
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
        },
    )


@receiver(delete_remote_image, sender='media.Media')
def ebay__image__delete(sender, instance, **kwargs):
    from products.models import Product
    from sales_channels.integrations.ebay.tasks_receiver_audit import (
        ebay__image__delete_db_task,
    )

    product_ids = list(instance.products.values_list("id", flat=True))
    products = Product.objects.filter(id__in=product_ids).only("id", "multi_tenant_company_id")

    for product in products.iterator():
        run_product_ebay_sales_channel_task_flow(
            task_func=ebay__image__delete_db_task,
            multi_tenant_company=product.multi_tenant_company,
            product=product,
            number_of_remote_requests=0,
            context={
                "image_id": instance.id,
                "product_id": product.id,
            },
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


@receiver(post_update, sender='ebay.EbayProductType')
def sales_channels__ebay_product_type__ensure_specific_rule(sender, instance: EbayProductType, **kwargs):
    if not instance.is_dirty_field(
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
