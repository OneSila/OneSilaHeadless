"""
ASGI config for OneSila project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/

This default file was adjusted to support websockets via strawberry channels.
"""
import os

from django.conf import settings

from django.core.asgi import get_asgi_application
from core.schema.routers import AuthGraphQLProtocolTypeRouter
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OneSila.settings")
django_application = get_asgi_application()


# Import your Strawberry schema after creating the django ASGI application
# This ensures django.setup() has been called before any ORM models are imported
# for the schema.
from .schema import schema  # NOQA
from .mcp import managed_mcp_app, mcp_lifespan  # NOQA

django_asgi = AuthGraphQLProtocolTypeRouter(
    schema,
    django_application=django_application,
    multipart_uploads_enabled=True,
)

starlette_app = Starlette(
    routes=[
        Mount("/mcp", app=managed_mcp_app),
        Mount("/", app=django_asgi),
    ],
    lifespan=lambda app: mcp_lifespan(app=app),
)

application = CORSMiddleware(
    starlette_app,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
)
