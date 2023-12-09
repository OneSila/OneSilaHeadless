import strawberry_django
from strawberry_django.relay import ListConnectionWithTotalCount
from strawberry.types import Info
from strawberry import type, field
from typing import Any, List
from .extensions import default_extensions


def anonymous_field(*args, **kwargs):
    return strawberry_django.field(*args, **kwargs)


def field(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def node(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.node(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
