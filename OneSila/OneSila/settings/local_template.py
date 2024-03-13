from .base import *

ALLOWED_HOSTS = ['myonesilaserver.com']
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
    # Or to allow everything:
    # '*',
    # IMPORTANT! In frontend Apollo client we need to specify we accept * so just adding  "http://localhost:3000" will be simpler
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
