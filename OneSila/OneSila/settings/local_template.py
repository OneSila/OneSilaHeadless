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
]

CORS_ALLOWED_HEADERS = [
    '*'
]

CORS_ALLOWED_METHODS = [
    '*'
]
