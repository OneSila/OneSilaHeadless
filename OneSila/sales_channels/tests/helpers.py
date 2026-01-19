from unittest.mock import patch


class TaskQueueDispatchPatchMixin:
    def setUp(self, *, _unused=None):
        super().setUp()
        self._task_queue_dispatch_patcher = patch(
            "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
            return_value=None,
        )
        self._task_queue_dispatch_patcher.start()
        self.addCleanup(self._task_queue_dispatch_patcher.stop)
