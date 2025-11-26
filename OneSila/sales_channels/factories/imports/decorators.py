import functools
from typing import Any, Callable


def if_allowed_by_saleschannel(setting: str) -> Callable:
    """
    Decorator that checks if a specific setting is enabled on the sales channel.
    If the setting is True, the decorated method is executed.
    Otherwise, the method returns None.

    Args:
        setting: The name of the attribute to check on the sales_channel

    Example:
        @if_allowed_by_saleschannel('sync_ean_codes')
        def handle_ean_code(self, import_instance):
            # This will only run if self.sales_channel.sync_ean_codes is True
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            if hasattr(self, 'sales_channel') and getattr(self.sales_channel, setting, False):
                return func(self, *args, **kwargs)
            return None
        return wrapper
    return decorator
