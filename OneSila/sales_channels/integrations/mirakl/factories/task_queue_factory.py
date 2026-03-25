from __future__ import annotations

from typing import Any

from core.huey import CRUCIAL_PRIORITY
from integrations.factories.task_queue import TaskQueueFactory
from integrations.helpers import get_import_path


class MiraklTaskQueueFactory(TaskQueueFactory):
    def __init__(
        self,
        *,
        sales_channel_id: int,
        task_func: Any,
        task_args: tuple | None = None,
        task_kwargs: dict | None = None,
        number_of_remote_requests: int | None = None,
        priority: int | None = None,
        sync_request_id: int | None = None,
    ) -> None:
        super().__init__(
            integration_id=sales_channel_id,
            task_func_path=get_import_path(task_func),
            task_args=task_args,
            task_kwargs=task_kwargs,
            number_of_remote_requests=number_of_remote_requests if number_of_remote_requests is not None else getattr(
                task_func,
                "number_of_remote_requests",
                1,
            ),
            priority=priority if priority is not None else getattr(task_func, "priority", CRUCIAL_PRIORITY),
            sync_request_id=sync_request_id,
        )
