from .base import *
import os
import tempfile

# Basic agent settings
DEBUG = True
SECRET_KEY = "dummy-secret-for-agent-tests"

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["http://localhost"]

# SQLite DB so no Postgres required
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(tempfile.gettempdir(), "agent.sqlite3"),
    }
}

# Static/media roots in /tmp
STATIC_ROOT = os.path.join(tempfile.gettempdir(), "static")
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), "media")
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
SAVE_TEST_FILES_ROOT = os.path.join(tempfile.gettempdir(), "testfiles")

# Email → dummy backend
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
EMAIL_FILE_PATH = os.path.join(tempfile.gettempdir(), "app-messages")

# CORS (safe defaults)
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CORS_ALLOWED_HEADERS = ["*"]
CORS_ALLOWED_METHODS = ["*"]
CORS_ALLOW_CREDENTIALS = True

# Strawberry
STRAWBERRY_DJANGO_REGISTER_USER_AUTO_LOGIN = False

# Huey → run inline
HUEY["immediate"] = True

# Logging → console only (avoid file paths)
LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
    "formatter": "verbose",
    "level": "DEBUG",
}
LOGGING["root"] = {
    "handlers": ["console"],
    "level": "INFO",
}

# Dummy values for required keys
LOCAL_HOST = "localhost:8000"
AI_POINT_PRICE = 0
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "dummy")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "dummy")

ADMIN_ROUTE_SUFFIX = "_agent"
SHOPIFY_SCOPES = ["read_products", "write_products"]
SHOPIFY_API_VERSION = "2025-04"
SHOPIFY_TEST_REDIRECT_URI = "http://localhost:8000/integrations/shopify/oauth/callback"

AMAZON_CLIENT_ID = None
AMAZON_CLIENT_SECRET = None
AMAZON_APP_ID = None
TEST_WEBHOOK_SECRET = "test-secret"


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}