from core.receivers import receiver
from core.signals import post_create, post_update
from sales_channels.integrations.mirakl.models import (
    MiraklProductCategory,
    MiraklProductType,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
)
from sales_channels.signals import (
    add_remote_product_variation,
    create_remote_document_association,
    create_remote_image_association,
    create_remote_product,
    create_remote_product_property,
    delete_remote_document,
    delete_remote_document_association,
    delete_remote_image,
    delete_remote_image_association,
    delete_remote_product,
    delete_remote_product_property,
    manual_sync_remote_product,
    refresh_website_pull_models,
    remove_remote_product_variation,
    sales_channel_created,
    sales_view_assign_updated,
    update_remote_image_association,
    update_remote_price,
    update_remote_product,
    update_remote_product_content,
    update_remote_product_eancode,
    update_remote_product_property,
)


def _get_remote_request_count(*, product) -> int:
    getter = getattr(product, "get_configurable_variations", None)
    if callable(getter):
        try:
            return 1 + getter().count()
        except Exception:  # pragma: no cover - defensive
            return 1
    return 1


@receiver(post_create, sender="mirakl.MiraklPropertySelectValue")
@receiver(post_update, sender="mirakl.MiraklPropertySelectValue")
def mirakl__property_select_value__propagate_local_mapping(sender, instance: MiraklPropertySelectValue, **kwargs):
    signal = kwargs.get("signal")
    if signal == post_update and not instance.is_dirty_field("local_instance", check_relationship=True):
        return
    if not instance.local_instance_id:
        return
    if not getattr(instance.remote_property, "local_instance_id", None):
        return

    from sales_channels.integrations.mirakl.factories.sync import (
        MiraklPropertySelectValueSiblingMappingFactory,
    )

    MiraklPropertySelectValueSiblingMappingFactory(
        remote_select_value=instance,
    ).run()


@receiver(post_update, sender="mirakl.MiraklProductType")
def mirakl__product_type__clone_remote_items(sender, instance: MiraklProductType, **kwargs):
    if not instance.is_dirty_field("remote_id"):
        return
    if not instance.remote_id or not instance.local_instance_id:
        return
    if instance.items.exists():
        return

    from sales_channels.integrations.mirakl.factories.sync import (
        MiraklProductTypeItemCloneFactory,
    )

    MiraklProductTypeItemCloneFactory(product_type=instance).run()


@receiver(post_create, sender="mirakl.MiraklProductCategory")
@receiver(post_update, sender="mirakl.MiraklProductCategory")
def mirakl__product_category__propagate_to_variations(sender, instance: MiraklProductCategory, **kwargs):
    product = getattr(instance, "product", None)
    if product is None or not product.is_configurable():
        return

    variations = product.get_configurable_variations(active_only=False)
    for variation in variations:
        MiraklProductCategory.objects.update_or_create(
            multi_tenant_company=instance.multi_tenant_company,
            product=variation,
            sales_channel=instance.sales_channel,
            defaults={
                "remote_id": instance.remote_id,
            },
        )


@receiver(refresh_website_pull_models, sender="sales_channels.SalesChannel")
@receiver(refresh_website_pull_models, sender="mirakl.MiraklSalesChannel")
@receiver(sales_channel_created, sender="sales_channels.SalesChannel")
@receiver(sales_channel_created, sender="mirakl.MiraklSalesChannel")
def sales_channels__mirakl__handle_pull(sender, instance, **kwargs):
    real_instance = instance.get_real_instance()
    if not isinstance(real_instance, MiraklSalesChannel):
        return

    if not real_instance.connected:
        return

    from sales_channels.integrations.mirakl.factories.sales_channels import (
        MiraklRemoteCurrencyPullFactory,
        MiraklRemoteLanguagePullFactory,
        MiraklSalesChannelViewPullFactory,
    )

    MiraklSalesChannelViewPullFactory(sales_channel=real_instance).run()
    MiraklRemoteLanguagePullFactory(sales_channel=real_instance).run()
    MiraklRemoteCurrencyPullFactory(sales_channel=real_instance).run()


@receiver(post_update, sender="mirakl.MiraklSalesChannelFeed")
def mirakl__feed__queue_processing_on_ready_to_render(sender, instance: MiraklSalesChannelFeed, **kwargs):
    if not instance.is_dirty_field("status"):
        return
    if instance.status != MiraklSalesChannelFeed.STATUS_READY_TO_RENDER:
        return
    if not getattr(instance.sales_channel, "active", False):
        return

    from sales_channels.integrations.mirakl.factories.task_queue import MiraklSingleChannelAddTask
    from sales_channels.integrations.mirakl.tasks import process_mirakl_feed_db_task

    task_runner = MiraklSingleChannelAddTask(
        task_func=process_mirakl_feed_db_task,
        sales_channel=instance.sales_channel,
        number_of_remote_requests=1,
    )
    task_runner.set_extra_task_kwargs(feed_id=instance.id)
    task_runner.run()


@receiver(manual_sync_remote_product, sender="sales_channels.RemoteProduct")
def mirakl__product__manual_sync(sender, instance, view=None, **kwargs):
    product = getattr(instance, "local_instance", None)
    if product is None or view is None:
        return

    resolved_view = view.get_real_instance()
    if resolved_view is None:
        return

    sales_channel = resolved_view.sales_channel.get_real_instance()

    from sales_channels.integrations.mirakl.factories.task_queue import MiraklSingleViewAddTask
    from sales_channels.integrations.mirakl.tasks import resync_mirakl_product_db_task

    if not isinstance(sales_channel, MiraklSalesChannel) or not sales_channel.active:
        return

    task_runner = MiraklSingleViewAddTask(
        task_func=resync_mirakl_product_db_task,
        view=resolved_view,
        number_of_remote_requests=_get_remote_request_count(product=product),
    )
    task_runner.set_extra_task_kwargs(
        product_id=product.id,
        remote_product_id=instance.id,
    )
    task_runner.run()


@receiver(manual_sync_remote_product, sender="mirakl.MiraklProduct")
def mirakl__mirakl_product__manual_sync(sender, instance, view=None, **kwargs):
    return mirakl__product__manual_sync(
        sender=sender,
        instance=instance,
        view=view,
        **kwargs,
    )


@receiver(create_remote_product, sender="sales_channels.SalesChannelViewAssign")
def mirakl__product__create_from_assign(sender, instance, view, **kwargs):
    sales_channel = instance.sales_channel.get_real_instance()
    if not isinstance(sales_channel, MiraklSalesChannel) or not sales_channel.active:
        return

    from sales_channels.integrations.mirakl.factories.task_queue import MiraklSingleViewAddTask
    from sales_channels.integrations.mirakl.tasks import create_mirakl_product_db_task

    task_runner = MiraklSingleViewAddTask(
        task_func=create_mirakl_product_db_task,
        view=view,
        number_of_remote_requests=_get_remote_request_count(product=instance.product),
    )
    task_runner.set_extra_task_kwargs(product_id=instance.product_id)
    task_runner.run()


@receiver(sales_view_assign_updated, sender="products.Product")
def mirakl__assign__update(sender, instance, sales_channel, view, **kwargs):
    sales_channel = sales_channel.get_real_instance()
    is_delete = kwargs.get("is_delete", False)
    if not isinstance(sales_channel, MiraklSalesChannel) or not sales_channel.active or is_delete:
        return

    from sales_channels.integrations.mirakl.factories.task_queue import MiraklSingleViewAddTask
    from sales_channels.integrations.mirakl.tasks import create_mirakl_product_db_task

    task_runner = MiraklSingleViewAddTask(
        task_func=create_mirakl_product_db_task,
        view=view,
        number_of_remote_requests=_get_remote_request_count(product=instance),
    )
    task_runner.set_extra_task_kwargs(product_id=instance.id)
    task_runner.run()


@receiver(delete_remote_product, sender="sales_channels.SalesChannelViewAssign")
def mirakl__product__delete_from_assign(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklSingleViewAddTask
    from sales_channels.integrations.mirakl.tasks import delete_mirakl_product_db_task

    sales_channel = instance.sales_channel.get_real_instance()
    if not isinstance(sales_channel, MiraklSalesChannel) or not sales_channel.active:
        return

    view = getattr(instance, "sales_channel_view", None)
    if view is None:
        return

    task_runner = MiraklSingleViewAddTask(
        task_func=delete_mirakl_product_db_task,
        view=view,
        number_of_remote_requests=_get_remote_request_count(product=instance.product),
    )
    task_runner.set_extra_task_kwargs(
        product_id=instance.product_id,
        remote_product_id=instance.remote_product_id,
    )
    task_runner.run()


@receiver(delete_remote_product, sender="products.Product")
def mirakl__product__delete_from_product(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductDeleteAddTask
    from sales_channels.integrations.mirakl.tasks import delete_mirakl_product_db_task

    task_runner = MiraklProductDeleteAddTask(
        task_func=delete_mirakl_product_db_task,
        local_instance_id=instance.id,
        multi_tenant_company=instance.multi_tenant_company,
        is_multiple=True,
    )
    task_runner.run()


@receiver(update_remote_product, sender="products.Product")
def mirakl__product__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductUpdateAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__product__update_db_task,
    )

    task_runner = MiraklProductUpdateAddTask(
        task_func=mirakl__product__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={"payload_keys": sorted(kwargs.keys())},
    )
    task_runner.run()


@receiver(create_remote_product_property, sender="properties.ProductProperty")
def mirakl__product_property__create(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductPropertyAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__product_property__create_db_task,
    )

    property_obj = getattr(instance, "property", None)
    task_runner = MiraklProductPropertyAddTask(
        task_func=mirakl__product_property__create_db_task,
        product=instance.product,
        product_property=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
            "value": instance.get_serialised_value(kwargs.get("language", None)),
        },
    )
    task_runner.run()


@receiver(update_remote_product_property, sender="properties.ProductProperty")
def mirakl__product_property__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductPropertyAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__product_property__update_db_task,
    )

    property_obj = getattr(instance, "property", None)
    task_runner = MiraklProductPropertyAddTask(
        task_func=mirakl__product_property__update_db_task,
        product=instance.product,
        product_property=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
            "payload_keys": sorted(kwargs.keys()),
            "value": instance.get_serialised_value(kwargs.get("language", None)),
        },
    )
    task_runner.run()


@receiver(delete_remote_product_property, sender="properties.ProductProperty")
def mirakl__product_property__delete(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductPropertyAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__product_property__delete_db_task,
    )

    property_obj = getattr(instance, "property", None)
    task_runner = MiraklProductPropertyAddTask(
        task_func=mirakl__product_property__delete_db_task,
        product=instance.product,
        product_property=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "product_property_id": instance.id,
            "property_id": getattr(property_obj, "id", None),
            "property_code": getattr(property_obj, "code", None),
            "value": instance.get_serialised_value(kwargs.get("language", None)),
        },
    )
    task_runner.run()


@receiver(update_remote_price, sender="products.Product")
def mirakl__price__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductPriceAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__price__update_db_task,
    )

    currency = kwargs.get("currency")
    task_runner = MiraklProductPriceAddTask(
        task_func=mirakl__price__update_db_task,
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


@receiver(update_remote_product_content, sender="products.Product")
def mirakl__content__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductContentAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__content__update_db_task,
    )

    language = kwargs.get("language")
    task_runner = MiraklProductContentAddTask(
        task_func=mirakl__content__update_db_task,
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


@receiver(update_remote_product_eancode, sender="products.Product")
def mirakl__ean_code__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductEanCodeAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__ean_code__update_db_task,
    )

    task_runner = MiraklProductEanCodeAddTask(
        task_func=mirakl__ean_code__update_db_task,
        product=instance,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(context=None)
    task_runner.run()


@receiver(add_remote_product_variation, sender="products.ConfigurableVariation")
def mirakl__variation__add(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductUpdateAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__variation__add_db_task,
    )

    task_runner = MiraklProductUpdateAddTask(
        task_func=mirakl__variation__add_db_task,
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


@receiver(remove_remote_product_variation, sender="products.ConfigurableVariation")
def mirakl__variation__remove(sender, parent_product, variation_product, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductUpdateAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__variation__remove_db_task,
    )

    task_runner = MiraklProductUpdateAddTask(
        task_func=mirakl__variation__remove_db_task,
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


@receiver(create_remote_image_association, sender="media.MediaProductThrough")
def mirakl__image_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductImagesAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__image_assoc__create_db_task,
    )

    media = getattr(instance, "media", None)
    task_runner = MiraklProductImagesAddTask(
        task_func=mirakl__image_assoc__create_db_task,
        product=instance.product,
        media_product_through_id=instance.id,
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


@receiver(update_remote_image_association, sender="media.MediaProductThrough")
def mirakl__image_assoc__update(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductImagesAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__image_assoc__update_db_task,
    )

    media = getattr(instance, "media", None)
    task_runner = MiraklProductImagesAddTask(
        task_func=mirakl__image_assoc__update_db_task,
        product=instance.product,
        media_product_through_id=instance.id,
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


@receiver(delete_remote_image_association, sender="media.MediaProductThrough")
def mirakl__image_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductImagesAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__image_assoc__delete_db_task,
    )

    media = getattr(instance, "media", None)
    task_runner = MiraklProductImagesAddTask(
        task_func=mirakl__image_assoc__delete_db_task,
        product=instance.product,
        media_product_through_id=instance.id,
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


@receiver(delete_remote_image, sender="media.Media")
def mirakl__image__delete(sender, instance, **kwargs):
    from products.models import Product
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductImagesAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__image__delete_db_task,
    )

    product_ids = list(instance.products.values_list("id", flat=True))
    products = Product.objects.filter(id__in=product_ids).only("id", "multi_tenant_company_id")
    for product in products.iterator():
        task_runner = MiraklProductImagesAddTask(
            task_func=mirakl__image__delete_db_task,
            product=product,
            media_product_through_id=None,
            number_of_remote_requests=0,
        )
        task_runner.set_extra_task_kwargs(
            context={
                "image_id": instance.id,
                "product_id": product.id,
            },
        )
        task_runner.run()


@receiver(create_remote_document_association, sender="media.MediaProductThrough")
def mirakl__document_assoc__create(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductDocumentsAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__document_assoc__create_db_task,
    )

    media = getattr(instance, "media", None)
    task_runner = MiraklProductDocumentsAddTask(
        task_func=mirakl__document_assoc__create_db_task,
        product=instance.product,
        media_product_through_id=instance.id,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
            "document_type_id": getattr(media, "document_type_id", None),
        },
    )
    task_runner.run()


@receiver(delete_remote_document_association, sender="media.MediaProductThrough")
def mirakl__document_assoc__delete(sender, instance, **kwargs):
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductDocumentsAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__document_assoc__delete_db_task,
    )

    media = getattr(instance, "media", None)
    task_runner = MiraklProductDocumentsAddTask(
        task_func=mirakl__document_assoc__delete_db_task,
        product=instance.product,
        media_product_through_id=instance.id,
        number_of_remote_requests=0,
    )
    task_runner.set_extra_task_kwargs(
        context={
            "media_product_through_id": instance.id,
            "media_id": getattr(media, "id", None),
            "media_type": getattr(media, "type", None),
            "document_type_id": getattr(media, "document_type_id", None),
        },
    )
    task_runner.run()


@receiver(delete_remote_document, sender="media.Media")
def mirakl__document__delete(sender, instance, **kwargs):
    from products.models import Product
    from sales_channels.integrations.mirakl.factories.task_queue import MiraklProductDocumentsAddTask
    from sales_channels.integrations.mirakl.tasks_receiver_audit import (
        mirakl__document__delete_db_task,
    )

    product_ids = list(instance.products.values_list("id", flat=True))
    products = Product.objects.filter(id__in=product_ids).only("id", "multi_tenant_company_id")
    for product in products.iterator():
        task_runner = MiraklProductDocumentsAddTask(
            task_func=mirakl__document__delete_db_task,
            product=product,
            media_product_through_id=None,
            number_of_remote_requests=0,
        )
        task_runner.set_extra_task_kwargs(
            context={
                "document_id": instance.id,
                "product_id": product.id,
            },
        )
        task_runner.run()
