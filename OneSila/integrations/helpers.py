import inspect
import importlib
from functools import lru_cache
from typing import Callable

from get_absolute_url.helpers import generate_absolute_url

from integrations.constants import INTEGRATIONS_TYPES_MAP, MAGENTO_INTEGRATION, MIRAKL_INTEGRATION
from integrations.models import PublicIntegrationType


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


def resolve_public_integration_lookup(*, integration) -> tuple[str, str | None]:
    instance = integration.get_real_instance() if hasattr(integration, "get_real_instance") else integration
    integration_type = INTEGRATIONS_TYPES_MAP.get(instance.__class__, MAGENTO_INTEGRATION)

    if integration_type != MIRAKL_INTEGRATION:
        return integration_type, None

    subtype = getattr(instance, "sub_type", None) or getattr(instance, "subtype", None) or None
    return MIRAKL_INTEGRATION, subtype


@lru_cache(maxsize=512)
def _get_public_integration_type_cached(*, integration_type: str, subtype: str | None):
    if integration_type == MIRAKL_INTEGRATION and subtype:
        public_integration_type = (
            PublicIntegrationType.objects
            .select_related("based_to")
            .prefetch_related("translations", "based_to__translations")
            .filter(type=MIRAKL_INTEGRATION, subtype=subtype)
            .first()
        )
        if public_integration_type is not None:
            return public_integration_type

    return (
        PublicIntegrationType.objects
        .select_related("based_to")
        .prefetch_related("translations", "based_to__translations")
        .filter(type=integration_type, subtype__isnull=True)
        .first()
    )


def get_public_integration_type_for_integration(*, integration):
    integration_type, subtype = resolve_public_integration_lookup(integration=integration)
    return _get_public_integration_type_cached(
        integration_type=integration_type,
        subtype=subtype,
    )


def get_public_integration_asset_url(*, integration, field_name: str) -> str | None:
    if isinstance(integration, PublicIntegrationType):
        public_integration_type = integration
    else:
        public_integration_type = get_public_integration_type_for_integration(integration=integration)

    if public_integration_type is None:
        return None

    file_field = getattr(public_integration_type, field_name, None)
    if not file_field:
        return None

    file_url = getattr(file_field, "url", None)
    if not file_url:
        return None

    return f"{generate_absolute_url(trailing_slash=False)}{file_url}"
