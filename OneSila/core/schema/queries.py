import strawberry_django
from strawberry_django.relay import ListConnectionWithTotalCount
from strawberry import type, field
from typing import Any
from .extensions import default_extensions


def field(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def node(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.node(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
