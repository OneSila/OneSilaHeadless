"""
Django settings for OneSila project.

Generated by 'django-admin startproject' using Django 4.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from django.utils.translation import gettext_lazy as _
from operator import itemgetter
import os

SECRET_KEY = "FAKE-KEY-DONT-KEEP-THIS-YOU-SHOULD-SET-A-NEW-ONE"

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'django.contrib.staticfiles',
    'strawberry_django',
    'django_cleanup.apps.CleanupConfig',
]

INSTALLED_LOCAL_APPS = [
    # Order matters!  The demo-data will run
    # through the list and some apps depend on others.
    # so not alphabetic order, but order according to dependency.
    'core',

    'contacts',
    'currencies',
    'taxes',
    'products',
    'products_inspector',
    'units',
    'translations',

    'customs',
    'billing',
    'eancodes',
    'lead_times',
    'llm',
    'media',
    'notifications',
    'integrations',
    'inventory',
    'sales_channels',
    'sales_channels.integrations.magento2',
    'sales_prices',
    'properties',
    'orders',

    'huey.contrib.djhuey',
]

INSTALLED_APPS += INSTALLED_LOCAL_APPS


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


AUTH_USER_MODEL = 'core.MultiTenantUser'


ROOT_URLCONF = 'OneSila.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'OneSila.wsgi.application'
ASGI_APPLICATION = 'OneSila.asgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_DB', 'fake'),
        'USER': os.getenv('POSTGRES_USER', 'fake'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'fake'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization of the interfaces
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('nl', _('Nederlands')),
    ('en', _('English')),
    # ('en-gb', _('English GB')),
)


TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_TZ = True

# Mails with errors go to...

ADMINS = [
    ("Sascha", 'sd@tweave.tech'),
    ("David", 'david@tweave.tech')
]

MANAGERS = ADMINS


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = 'media/'

# Forced here for test-deployment purposes
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
SAVE_TEST_FILES_ROOT = os.path.join(BASE_DIR, 'test_files_root')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#
# Strawberry graphql settings
#

MULTI_TENANT_LOGIN_LINK_EXPIRES_AFTER_MIN = 60

STRAWBERRY_DJANGO = {
    "FIELD_DESCRIPTION_FROM_HELP_TEXT": True,
    "TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING": True,
    "MAP_AUTO_ID_AS_GLOBAL_ID": True,
    "USE_DEPRECATED_FILTERS": False,
}

# https://channels.readthedocs.io/en/stable/topics/channel_layers.html
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv('REDIS_HOST', "127.0.0.1"), os.getenv('REDIS_PORT', 6379))],
        },
    },
}

#
# Default CORS settings
#

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    '*',
    # 'http://172.19.250.107:3000',
]

CORS_ALLOWED_HEADERS = [
    '*'
]

CORS_ALLOWED_METHODS = [
    '*'
]


HUEY = {
    'huey_class': 'huey.RedisHuey',
    'name': 'hueyonesilaheadless',
    'results': True,  # Store return values of tasks.
    'store_none': False,
    'immediate': True,  # KEEP AS TRUE, AND OVERRIDE YOUR LOCAL FILE WITH FALSE. CHANGE THIS AND YOUR TESTS WILL FAIL.
    'utc': True,
    'blocking': True,  # Perform blocking pop rather than poll Redis.
    'connection': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'connection_pool': None,  # Definitely you should use pooling!
        # ... tons of other options, see redis-py for details.

        # huey-specific connection parameters.
        'read_timeout': 1,  # If not polling (blocking pop), use timeout.
        'url': None,  # Allow Redis config via a DSN.
    },
    'consumer': {
        'workers': 1,
        'worker_type': 'thread',
        'initial_delay': 0.1,
        'backoff': 1.15,
        'max_delay': 10.0,
        'scheduler_interval': 1,
        'periodic': True,
        'check_worker_health': True,
        'health_check_interval': 1,
    },
}
