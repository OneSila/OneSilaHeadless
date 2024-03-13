"""
ASGI config for OneSila project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/

This default file was adjusted to support websockets via strawberry channels.
"""
from .schema import schema
import os
from django.conf import settings

from django.core.asgi import get_asgi_application
from strawberry_django.routers import AuthGraphQLProtocolTypeRouter
from starlette.middleware.cors import CORSMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OneSila.settings")
django_application = get_asgi_application()


# Import your Strawberry schema after creating the django ASGI application
# This ensures django.setup() has been called before any ORM models are imported
# for the schema.
application = AuthGraphQLProtocolTypeRouter(
    schema,
    django_application=django_application,
)

application = CORSMiddleware(
    application,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS
)
