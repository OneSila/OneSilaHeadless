"""Retry helpers for Shein integration requests."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


def retry_shein_request(
    *,
    max_retries: int = 2,
    base_delay: float = 2.0,
    retry_exceptions: Optional[tuple[type[Exception], ...]] = None,
) -> Callable:
    """Retry decorated callables for transient request failures."""

    exceptions = retry_exceptions or (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
    )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "Shein request failed (%s/%s). Retrying in %.1fs.",
                        attempt + 1,
                        max_retries + 1,
                        delay,
                        exc_info=exc,
                    )
                    time.sleep(delay)

        return wrapper

    return decorator
