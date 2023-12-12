from strawberry_django.resolvers import django_resolver
from asgiref.sync import async_to_sync
from core.factories.multi_tenant import RegisterUserFactory
from strawberry_django.utils.requests import get_request
from channels import auth as channels_auth
from django.contrib import auth

from .mutation_classes import CleanupDataMixin


@django_resolver
def resolve_register_user(info, username: str, password: str, language: str):
    request = get_request(info)

    fac = RegisterUserFactory(username=username, password=password, language=language)
    fac.run()

    user = fac.user

    try:
        # We dont have any need for the classic django-auth outside of the
        # tests.  So this is why this try except clause exists.
        auth.login(request, user)
    except AttributeError:
        # ASGI in combo with websockets needs the channels login functionality.
        # to ensure we're talking about channels, let's veriy that our
        # request is actually channelsrequest
        try:
            scope = request.consumer.scope  # type: ignore
            async_to_sync(channels_auth.login)(scope, user)  # type: ignore
            # According to channels docs you must save the session
            scope["session"].save()
        except (AttributeError, NameError):
            # When Django-channels is not installed,
            # this code will be non-existing
            pass
    return user
