import strawberry_django
from strawberry_django.permissions import IsAuthenticated


def field(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
