
from .base import *

ALLOWED_HOSTS = ['myonesilaserver.com']
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]
DEBUG = True

import sentry_sdk
SENTRY_DSN = "xxx"
SENTRY_CONFIG["dsn"] = SENTRY_DSN
sentry_sdk.init(**SENTRY_CONFIG)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'onesila',
        'USER': 'onesila',
        'PASSWORD': 'my-complicated-pass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


STATIC_ROOT = '/home/onesila/static/'
MEDIA_ROOT = '/home/onesila/mediafiles/'
APP_ROOT = '/home/onesila/OneSilaHeadless/OneSila/'
SAVE_TEST_FILES_ROOT = '/home/onesila/testfiles/'

#
# Localhost settings if your localhost has poor hostname resolve for
# image and absolute url settings. https://github.com/TweaveTech/django_get_absolute_url
#
# HTTPS_SUPPORTED = False
# LOCAL_HOST = 'localhost:8080'

SECRET_KEY = 'your-secret-key-goes-here'

#
# Url generation settings
#

HTTPS_SUPPORTED = True

# Email setup
#
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'  # change this to a proper location

#
# CORS Settings. See: https://www.starlette.io/middleware/#corsmiddleware
#

CORS_ALLOWED_ORIGINS = [
    # Format example:
    # 'http://172.19.250.107:3000',
    # the right port will depend on the port the frontend is running.
    # on a dev machine check npm run dev and add that here.
    "http://localhost:5173",
]

CORS_ALLOWED_HEADERS = [
    '*'
]

CORS_ALLOWED_METHODS = [
    '*'
]

# This allows session information to be passed through to the queries
# to ensure login via django-sessions.
CORS_ALLOW_CREDENTIALS = True


#
# Strawberry override
#

STRAWBERRY_DJANGO_REGISTER_USER_AUTO_LOGIN = False


#
# How long should the login link stay valid for?
#
MULTI_TENANT_LOGIN_LINK_EXPIRES_AFTER_MIN = 60


#
# Huey overrides
#
HUEY['immediate'] = DEBUG

#
# Logging
#
LOGGING['handlers']['amazon_log_file'] = {
    'class': 'logging.FileHandler',
    'formatter': 'verbose',
    'level': 'DEBUG',
    'filename': '/var/log/OneSilaHeadless/sales_channels_integrations_amazon.log',
}

# This will make absolute path to work
LOCAL_HOST = 'localhost:8080'

# price per ai point
AI_POINT_PRICE = 0
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REPLICATE_API_TOKEN = ""

ADMIN_ROUTE_SUFFIX = "_somethingSecure"

SHOPIFY_SCOPES = ['read_products', 'write_products']
SHOPIFY_API_VERSION = "2025-04"
SHOPIFY_TEST_REDIRECT_URI = "https://dcfa-79-118-110-129.ngrok-free.app/integrations/shopify/oauth/callback"


AMAZON_CLIENT_ID = None
AMAZON_CLIENT_SECRET = None
AMAZON_APP_ID = None

SHEIN_APP_ID = None
SHEIN_REDIRECT_URI = "https://your-domain/integrations/shein/oauth/callback"
SHEIN_APP_SECRET = None

EBAY_CLIENT_ID = None
EBAY_CLIENT_SECRET = None
EBAY_DEV_ID = None
EBAY_APPLICATION_SCOPES = ["https://api.ebay.com/oauth/api_scope"]
EBAY_RU_NAME = 'Name'
EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN = "replace-with-onesila-ebay-verification-token-123456"

TEST_WEBHOOK_SECRET = "test-secret"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"