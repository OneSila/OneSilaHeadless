import inspect
import importlib
from typing import Callable


def resolve_function(path: str) -> Callable:
    """
    Resolves and returns a callable (function or class) from a given import path string.

    :param path: The import path of the function or class (e.g., 'module.submodule.function_name')
    :return: The callable object
    :raises ImportError: If the module cannot be imported
    :raises AttributeError: If the function or class cannot be found in the module
    """
    module_path, func_name = path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def get_import_path(obj):
    """
    Returns the import path of an object (function or class) as a string.

    :param obj: The function, class, or task object to get the import path for.
    :return: The import path as a string.
    """
    # Check if obj is a TaskWrapper or similar object from Huey
    if hasattr(obj, 'func'):
        # Use the function directly from the task wrapper
        obj = obj.func

    # If the object is a class type, use __module__ and __qualname__
    if hasattr(obj, 'task_class'):
        return f"{obj.task_class.__module__}.{obj.task_class.__name__}"

    # Standard approach for functions and classes
    module = inspect.getmodule(obj)
    if module is None:
        raise ValueError(f"Could not determine the module for object {obj}")

    module_path = module.__name__
    # Use __qualname__ for qualified names (handles nested classes/functions)
    if hasattr(obj, '__qualname__'):
        return f"{module_path}.{obj.__qualname__}"
    elif hasattr(obj, '__name__'):
        return f"{module_path}.{obj.__name__}"
    else:
        raise ValueError(f"Could not determine the name for object {obj}")
