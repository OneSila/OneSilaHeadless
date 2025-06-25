import time
from functools import wraps
from sp_api.base import SellingApiRequestThrottledException

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
                except SellingApiRequestThrottledException as e:
                    if attempt >= max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    return None
            return None

        return wrapper
    return decorator
