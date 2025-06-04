from functools import wraps
from .exceptions import NoneValueNotAllowedError


def raise_for_none(arg_name):
    """
    Decorator that checks if an argument or keyword argument has None value.
    Raises NoneValueNotAllowedError if the value is None.

    Args:
        arg_name (str): Name of the argument to check
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check kwargs first
            if arg_name in kwargs and kwargs[arg_name] is None:
                raise NoneValueNotAllowedError(f"Argument '{arg_name}' cannot be None")

            # Get function arg names to check positional args
            import inspect
            arg_names = inspect.getfullargspec(func).args
            try:
                arg_index = arg_names.index(arg_name)
                if arg_index < len(args) and args[arg_index] is None:
                    raise NoneValueNotAllowedError(f"Argument '{arg_name}' cannot be None")
            except ValueError:
                pass

            return func(*args, **kwargs)
        return wrapper
    return decorator
