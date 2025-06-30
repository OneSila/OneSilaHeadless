import time
from functools import wraps
from sp_api.base import SellingApiRequestThrottledException
from spapi.rest import ApiException
import requests


def throttle_safe(max_retries=5, base_delay=1.0):
    """
    Decorator to retry the decorated function if throttled (HTTP 429).
    Uses exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (SellingApiRequestThrottledException, requests.exceptions.RequestException):
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                except ApiException as exc:
                    status = getattr(exc, "status", None)
                    if status != 500 or attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue

        return wrapper
    return decorator
