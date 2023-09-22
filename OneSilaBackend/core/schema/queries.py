import strawberry_django
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.relay import ListConnectionWithTotalCount
from strawberry import type


def field(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def node(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.node(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
