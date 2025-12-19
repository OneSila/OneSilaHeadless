from huey.contrib.djhuey import db_task

from core.huey import MEDIUM_PRIORITY
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.decorators import remote_task


def _ebay_receiver_audit_execute(
    task_queue_item_id: int,
    *,
    event_name: str,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    from sales_channels.factories.receiver_audit import RemoteReceiverAuditFactory
    from sales_channels.integrations.ebay.models import (
        EbayProduct,
        EbaySalesChannel,
        EbaySalesChannelView,
    )

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        sales_channel = EbaySalesChannel.objects.get(id=sales_channel_id)
        resolved_view_id = view_id or sales_channel_view_id
        view = EbaySalesChannelView.objects.get(id=resolved_view_id) if resolved_view_id else None
        remote_product = EbayProduct.objects.select_related("local_instance").get(id=remote_product_id)

        RemoteReceiverAuditFactory(
            integration_label="eBay",
            event_name=event_name,
            sales_channel=sales_channel,
            view=view,
            remote_product=remote_product,
            context=context,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__product__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__product__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__product_property__create_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__product_property__create",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__product_property__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__product_property__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__product_property__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__product_property__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__price__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__price__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__content__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__content__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__ean_code__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__ean_code__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__variation__add_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__variation__add",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__variation__remove_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__variation__remove",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__image_assoc__create_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__image_assoc__create",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__image_assoc__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__image_assoc__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__image_assoc__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__image_assoc__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def ebay__image__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    view_id: int | None = None,
    sales_channel_view_id: int | None = None,
    context: dict | None = None,
) -> None:
    _ebay_receiver_audit_execute(
        task_queue_item_id,
        event_name="ebay__image__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        view_id=view_id,
        sales_channel_view_id=sales_channel_view_id,
        context=context,
    )

