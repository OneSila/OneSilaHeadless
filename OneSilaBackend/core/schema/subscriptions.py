import strawberry_django

from strawberry import type, subscription
from strawberry.types import Info
from typing import List, AsyncGenerator

from asgiref.sync import sync_to_async
import asyncio

from strawberry_django.permissions import IsAuthenticated
from strawberry_django.relay import ListConnectionWithTotalCount


def field(*args, **kwargs):
    extensions = []
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def node(*args, **kwargs):
    extensions = []
    return strawberry_django.node(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = []
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
