
from .base import *

ALLOWED_HOSTS = ['myonesilaserver.com']
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]
DEBUG = True

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

# This will make absolute path to work
LOCAL_HOST = 'localhost:8080'

# price per ai point
AI_POINT_PRICE = 0
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REPLICATE_API_TOKEN=""

ADMIN_ROUTE_SUFFIX = "_somethingSecure"

SHOPIFY_API_KEY ="xxx"
SHOPIFY_API_SECRET = "xxx"
SHOPIFY_SCOPES = ['read_products', 'write_products']
SHOPIFY_API_VERSION = "2024-07"
SHOPIFY_TEST_REDIRECT_URI = "https://dcfa-79-118-110-129.ngrok-free.app/integrations/shopify/oauth/callback"