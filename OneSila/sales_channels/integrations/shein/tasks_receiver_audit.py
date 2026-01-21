from huey.contrib.djhuey import db_task

from core.huey import MEDIUM_PRIORITY
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.decorators import remote_task


def _shein_receiver_audit_execute(
    task_queue_item_id: int,
    *,
    event_name: str,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    from sales_channels.factories.receiver_audit import RemoteReceiverAuditFactory
    from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task():
        sales_channel = SheinSalesChannel.objects.get(id=sales_channel_id)
        remote_product = SheinProduct.objects.select_related("local_instance").get(id=remote_product_id)

        RemoteReceiverAuditFactory(
            integration_label="Shein",
            event_name=event_name,
            sales_channel=sales_channel,
            remote_product=remote_product,
            context=context,
        )

    task.execute(actual_task)


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__product__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__product__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__product_property__create_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__product_property__create",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__product_property__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__product_property__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__product_property__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__product_property__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__price__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__price__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__content__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__content__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__ean_code__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__ean_code__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__variation__add_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__variation__add",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__variation__remove_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__variation__remove",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__image_assoc__create_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__image_assoc__create",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__image_assoc__update_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__image_assoc__update",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__image_assoc__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__image_assoc__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )


@remote_task(priority=MEDIUM_PRIORITY, number_of_remote_requests=0)
@db_task()
def shein__image__delete_db_task(
    task_queue_item_id: int,
    *,
    sales_channel_id: int,
    remote_product_id: int,
    context: dict | None = None,
) -> None:
    _shein_receiver_audit_execute(
        task_queue_item_id,
        event_name="shein__image__delete",
        sales_channel_id=sales_channel_id,
        remote_product_id=remote_product_id,
        context=context,
    )
