"""
ASGI config for OneSila project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/

This default file was adjusted to support websockets via strawberry channels.
"""


from .schema import schema
import os

from django.core.asgi import get_asgi_application
from strawberry_django.routers import AuthGraphQLProtocolTypeRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OneSila.settings")
django_asgi_app = get_asgi_application()

# Import your Strawberry schema after creating the django ASGI application
# This ensures django.setup() has been called before any ORM models are imported
# for the schema.


application = AuthGraphQLProtocolTypeRouter(
    schema,
    django_application=django_asgi_app,
)
