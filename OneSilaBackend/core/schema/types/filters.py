from strawberry_django.filters import filter as strawberry_filter


def filter(*args, lookups=True, **kwargs):
    return strawberry_filter(*args, **kwargs, lookups=lookups)
