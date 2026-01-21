from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.integrations.shein.models import SheinSalesChannel, SheinProperty
from sales_channels.integrations.shein.factories.sync.rule_sync import (
    SheinPropertyRuleItemSyncFactory,
)
from sales_channels.signals import (
    create_remote_product,
    create_remote_product_property,
    delete_remote_image,
    delete_remote_image_association,
    delete_remote_product_property,
    manual_sync_remote_product,
    add_remote_product_variation,
    create_remote_image_association,
    remove_remote_product_variation,
    refresh_website_pull_models,
    sales_channel_created,
    update_remote_image_association,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_eancode,
    update_remote_product_property,
)

from sales_channels.integrations.shein.flows.internal_properties import (
    ensure_internal_properties_flow,
)


@receiver(refresh_website_pull_models, sender='sales_channels.SalesChannel')
@receiver(refresh_website_pull_models, sender='shein.SheinSalesChannel')
@receiver(sales_channel_created, sender='sales_channels.SalesChannel')
@receiver(sales_channel_created, sender='shein.SheinSalesChannel')
def sales_channels__shein__handle_pull(sender, instance, **kwargs):
    real_instance = instance.get_real_instance()
    if not isinstance(real_instance, SheinSalesChannel):
        return

    from sales_channels.integrations.shein.factories.sales_channels import  SheinSalesChannelViewPullFactory

    SheinSalesChannelViewPullFactory(sales_channel=instance).run()
    ensure_internal_properties_flow(real_instance)


@receiver(post_create, sender='shein.SheinProductCategory')
@receiver(post_update, sender='shein.SheinProductCategory')
def shein__product_category__propagate_to_variations(sender, instance, **kwargs):
    """
    When a Shein category is assigned to a configurable (parent) product,
    automatically propagate it to all its variations.
    """
    from sales_channels.integrations.shein.models import SheinProductCategory

    if not instance.product.is_configurable():
        return

    variations = instance.product.get_configurable_variations(active_only=False)
    for variation in variations:
        SheinProductCategory.objects.get_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            sales_channel=instance.sales_channel,
            defaults={
                "remote_id": instance.remote_id,
            },
        )


@receiver(manual_sync_remote_product, sender='sales_channels.RemoteProduct')
def shein__product__manual_sync(
    sender,
    instance,
    view=None,
    **kwargs,
):
    product = getattr(instance, "local_instance", None)
    if product is None:
        return

    sales_channel = getattr(instance, "sales_channel", None)
    if sales_channel is not None:
        sales_channel = sales_channel.get_real_instance()
    elif view is not None:
        resolved_view = view.get_real_instance()
        if resolved_view is None:
            return
        sales_channel = resolved_view.sales_channel.get_real_instance()
    else:
        return

    from sales_channels.integrations.shein.factories.task_queue import SheinSingleChannelAddTask
    from sales_channels.integrations.shein.tasks import resync_shein_product_db_task

    if not isinstance(sales_channel, SheinSalesChannel) or not sales_channel.active:
        return

    count = 1 + getattr(product, 'get_configurable_variations', lambda: [])().count()

    task_runner = SheinSingleChannelAddTask(
        task_func=resync_shein_product_db_task,
        sales_channel=sales_channel,
        number_of_remote_requests=count,
    )
    task_runner.set_extra_task_kwargs(
        product_id=product.id,
        remote_product_id=instance.id,
    )
    task_runner.run()


@receiver(manual_sync_remote_product, sender="shein.SheinProduct")
def shein__shein_product__manual_sync(
    sender,
    instance,
    view=None,
    **kwargs,
):
    # Delegate to the generic receiver for backwards compatibility.
    return shein__product__manual_sync(
        sender=sender,
        instance=instance,
        view=view,
        **kwargs,
    )


@receiver(update_remote_product, sender='products.Product')
def shein__product__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__product__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductUpdateAddTask

    task_runner = SheinProductUpdateAddTask(
        task_func=shein__product__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={"payload_keys": sorted(kwargs.keys())},
    )
    task_runner.run()


@receiver(create_remote_product_property, sender='properties.ProductProperty')
def shein__product_property__create(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__product_property__create_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductPropertyAddTask

    product = instance.product
    property_obj = getattr(instance, "property", None)
    task_runner = SheinProductPropertyAddTask(
        task_func=shein__product_property__create_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
        },
    )
    task_runner.run()


@receiver(update_remote_product_property, sender='properties.ProductProperty')
def shein__product_property__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__product_property__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductPropertyAddTask

    product = instance.product
    property_obj = getattr(instance, "property", None)
    task_runner = SheinProductPropertyAddTask(
        task_func=shein__product_property__update_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
            "payload_keys": sorted(kwargs.keys()),
        },
    )
    task_runner.run()


@receiver(delete_remote_product_property, sender='properties.ProductProperty')
def shein__product_property__delete(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__product_property__delete_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductPropertyAddTask

    product = instance.product
    property_obj = getattr(instance, "property", None)
    task_runner = SheinProductPropertyAddTask(
        task_func=shein__product_property__delete_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
        },
    )
    task_runner.run()


@receiver(update_remote_price, sender='products.Product')
def shein__price__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__price__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductPriceAddTask

    currency = kwargs.get("currency")
    task_runner = SheinProductPriceAddTask(
        task_func=shein__price__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "currency_id": getattr(currency, "id", None),
            "currency_code": getattr(currency, "code", None),
            "currency_iso_code": getattr(currency, "iso_code", None),
        },
    )
    task_runner.run()


@receiver(update_remote_product_content, sender='products.Product')
def shein__content__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__content__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductContentAddTask

    language = kwargs.get("language")
    task_runner = SheinProductContentAddTask(
        task_func=shein__content__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "language_id": getattr(language, "id", None),
            "language_code": getattr(language, "code", None),
            "language_iso_code": getattr(language, "iso_code", None),
        },
    )
    task_runner.run()


@receiver(update_remote_product_eancode, sender='products.Product')
def shein__ean_code__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__ean_code__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductEanCodeAddTask

    task_runner = SheinProductEanCodeAddTask(
        task_func=shein__ean_code__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(context=None)
    task_runner.run()


@receiver(add_remote_product_variation, sender='products.ConfigurableVariation')
def shein__variation__add(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__variation__add_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductUpdateAddTask

    task_runner = SheinProductUpdateAddTask(
        task_func=shein__variation__add_db_task,
        product=parent_product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "parent_product_id": getattr(parent_product, "id", None),
            "variation_product_id": getattr(variation_product, "id", None),
        },
    )
    task_runner.run()


@receiver(remove_remote_product_variation, sender='products.ConfigurableVariation')
def shein__variation__remove(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__variation__remove_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductUpdateAddTask

    task_runner = SheinProductUpdateAddTask(
        task_func=shein__variation__remove_db_task,
        product=parent_product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "parent_product_id": getattr(parent_product, "id", None),
            "variation_product_id": getattr(variation_product, "id", None),
        },
    )
    task_runner.run()


@receiver(create_remote_image_association, sender='media.MediaProductThrough')
def shein__image_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__image_assoc__create_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductImagesAddTask

    product = instance.product
    media = getattr(instance, "media", None)
    task_runner = SheinProductImagesAddTask(
        task_func=shein__image_assoc__create_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
        },
    )
    task_runner.run()


@receiver(update_remote_image_association, sender='media.MediaProductThrough')
def shein__image_assoc__update(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__image_assoc__update_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductImagesAddTask

    product = instance.product
    media = getattr(instance, "media", None)
    task_runner = SheinProductImagesAddTask(
        task_func=shein__image_assoc__update_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
            "payload_keys": sorted(kwargs.keys()),
        },
    )
    task_runner.run()


@receiver(delete_remote_image_association, sender='media.MediaProductThrough')
def shein__image_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__image_assoc__delete_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductImagesAddTask

    product = instance.product
    media = getattr(instance, "media", None)
    task_runner = SheinProductImagesAddTask(
        task_func=shein__image_assoc__delete_db_task,
        product=product,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
        },
    )
    task_runner.run()


@receiver(delete_remote_image, sender='media.Media')
def shein__image__delete(sender, instance, **kwargs):
    from products.models import Product
    from sales_channels.integrations.shein.tasks_receiver_audit import (
        shein__image__delete_db_task,
    )
    from sales_channels.integrations.shein.factories.task_queue import SheinProductImagesAddTask

    product_ids = list(instance.products.values_list("id", flat=True))
    products = Product.objects.filter(id__in=product_ids).only("id", "multi_tenant_company_id")

    for product in products.iterator():
        task_runner = SheinProductImagesAddTask(
            task_func=shein__image__delete_db_task,
            product=product,
            number_of_remote_requests=0,
        )
        task_runner.set_extra_task_kwargs(
            context={
                "image_id": instance.id,
                "product_id": product.id,
            },
        )
        task_runner.run()


@receiver(post_create, sender="shein.SheinProperty")
@receiver(post_update, sender="shein.SheinProperty")
def sales_channels__shein_property__sync_rule_item(
    *,
    sender,
    instance: SheinProperty,
    **kwargs,
):
    """Sync ProductPropertiesRuleItem when a Shein property is mapped locally."""
    signal = kwargs.get("signal")
    if signal == post_update and not instance.is_dirty_field(
        "local_instance",
        check_relationship=True,
    ):
        return
    if signal == post_create and not instance.local_instance:
        return

    SheinPropertyRuleItemSyncFactory(shein_property=instance).run()
