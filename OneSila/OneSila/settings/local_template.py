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
# CORS headers and OPTIONS Request.
#

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
