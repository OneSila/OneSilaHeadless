"""Helpers for queuing Shein product tasks."""

from django.db import transaction

from integrations.helpers import get_import_path
from integrations.tasks import add_task_to_queue


def run_single_shein_product_task_flow(
    *,
    task_func,
    sales_channel,
    number_of_remote_requests=None,
    **kwargs,
) -> None:
    """Queue a task for a specific Shein product."""

    task_kwargs = {
        "sales_channel_id": sales_channel.id,
        **kwargs,
    }

    transaction.on_commit(
        lambda lb_task_kwargs=task_kwargs, integration_id=sales_channel.id: add_task_to_queue(
            integration_id=integration_id,
            task_func_path=get_import_path(task_func),
            task_kwargs=lb_task_kwargs,
            number_of_remote_requests=number_of_remote_requests,
        )
    )
