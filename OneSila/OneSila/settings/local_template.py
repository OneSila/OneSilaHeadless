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

# to allow local enviroment connect backend and frontend
CORS_ALLOW_ALL_ORIGINS = True