from .base import *

ALLOWED_HOSTS = ['*', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mydb',
        'USER': 'mydb_user',
        'PASSWORD': 'somedbpass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

SECRET_KEY = 'your-secret-key-goes-here'


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
