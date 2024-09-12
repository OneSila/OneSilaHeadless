from functools import wraps
from core.huey import DEFAULT_PRIORITY


def remote_task(priority=DEFAULT_PRIORITY, number_of_remote_requests=1):
    """
    Decorator to set metadata on task functions for priority and number_of_remote_requests.

    :param priority: The priority of the task.
    :param number_of_remote_requests: The number of remote requests the task makes.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach the metadata
        wrapper.priority = priority
        wrapper.number_of_remote_requests = number_of_remote_requests
        return wrapper

    return decorator
