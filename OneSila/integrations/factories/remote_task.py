import logging
import traceback
from integrations.models import IntegrationTaskQueue

logger = logging.getLogger(__name__)

class BaseRemoteTask:
    def __init__(self, task_queue_item_id):
        self.task_queue_item_id = task_queue_item_id
        self.task_queue_item = self.get_task_queue_item()

    def get_task_queue_item(self):
        try:
            return IntegrationTaskQueue.objects.get(id=self.task_queue_item_id)
        except IntegrationTaskQueue.DoesNotExist:
            error_message = f"IntegrationTaskQueue item with ID {self.task_queue_item_id} does not exist."
            logger.error(error_message)
            # Raise an exception to ensure this critical error is caught and handled
            raise IntegrationTaskQueue.DoesNotExist(error_message)

    def execute(self, task_func, *args, **kwargs):
        """Executes the provided task function and handles success or failure."""
        try:
            task_func(*args, **kwargs)
            self.task_queue_item.mark_as_processed()
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error executing task '{self.task_queue_item.task_name}': {str(e)}\n{tb}")
            self.task_queue_item.mark_as_failed(error_message=str(e), error_traceback=tb)
