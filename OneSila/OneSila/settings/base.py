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
import sys

SECRET_KEY = "FAKE-KEY-DONT-KEEP-THIS-YOU-SHOULD-SET-A-NEW-ONE"

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False
TESTING = 'test' in sys.argv

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
    'imports_exports',
    'llm',
    'media',
    'notifications',
    'integrations',
    'inventory',
    'sales_channels',
    'sales_channels.integrations.magento2',
    'sales_channels.integrations.shopify',
    'sales_channels.integrations.woocommerce',
    'sales_channels.integrations.amazon',
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

#
# Session settings. Effort to fix session issues across multiple workers.
# By default we keep the default django cache stuff.
# but sessions let's move the elsewhere.
#

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "onesila_session_cache"

REDIS_HOST = os.getenv('REDIS_HOST', "127.0.0.1")
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "onesila_session_cache": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
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

# the languages the interface is translated on
INTERFACE_LANGUAGES = (
    ('en', _('English')),
    ('nl', _('Dutch')),
)

LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
    ('nl', _('Dutch')),
    ('de', _('German')),
    ('it', _('Italian')),
    ('es', _('Spanish')),
    ('pt', _('Portuguese')),
    ('pl', _('Polish')),
    ('ro', _('Romanian')),
    ('bg', _('Bulgarian')),
    ('hr', _('Croatian')),
    ('cs', _('Czech')),
    ('da', _('Danish')),
    ('et', _('Estonian')),
    ('fi', _('Finnish')),
    ('el', _('Greek')),
    ('hu', _('Hungarian')),
    ('lv', _('Latvian')),
    ('lt', _('Lithuanian')),
    ('sk', _('Slovak')),
    ('sl', _('Slovenian')),
    ('sv', _('Swedish')),
    ('th', _('Thai')),
    ('ja', _('Japanese')),
    ('zh-hans', _('Chinese (Simplified)')),
    ('hi', _('Hindi')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('ru', _('Russian')),
    ('af', _('Afrikaans')),
    ('ar', _('Arabic')),
    ('he', _('Hebrew')),
    ('tr', _('Turkish')),
    ('id', _('Indonesian')),
    ('ko', _('Korean')),
    ('ms', _('Malay')),
    ('vi', _('Vietnamese')),
    ('fa', _('Persian')),
    ('ur', _('Urdu')),
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
            "hosts": [f"redis://{REDIS_HOST}:{REDIS_PORT}/3"],
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

#
# Default User Agent.  Used by integrations to identify the source of the request.
#

ONESILA_DEFAULT_USER_AGENT = "OneSila.com PIM/1.0"


#
# Integrations test settings
#

SALES_CHANNELS_INTEGRATIONS_TEST_STORES = {
    'WOOCOMMERCE': {
        'hostname': os.getenv('INTEGRATIONS_TEST_STORES_WOOCOMMERCE_HOSTNAME'),
        'api_key': os.getenv('INTEGRATIONS_TEST_STORES_WOOCOMMERCE_API_KEY'),
        'api_secret': os.getenv('INTEGRATIONS_TEST_STORES_WOOCOMMERCE_API_SECRET'),
        'verify_ssl': False,
        'requests_per_minute': 60,
        'active': True,
        'import_products': True,
        'import_orders': True,
        'api_version': 'wc/v3',
        'timeout': 10,
    }
}

#
# Huey settings
#
HUEY = {
    'huey_class': 'huey.RedisHuey',
    'name': 'hueyonesilaheadless',
    'results': True,  # Store return values of tasks.
    'store_none': False,
    'immediate': True,  # KEEP AS TRUE, AND OVERRIDE YOUR LOCAL FILE WITH FALSE. CHANGE THIS AND YOUR TESTS WILL FAIL.
    'utc': True,
    'blocking': True,  # Perform blocking pop rather than poll Redis.
    'connection': {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
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


#
# Admin url suffix.
#

ADMIN_ROUTE_SUFFIX = os.getenv('ADMIN_ROUTE_SUFFIX', "")

#
# Magento integration settings (sales_channels.integrations.magento2)
#

MAGENTO_LOG_DIR_PATH = os.getenv('MAGENTO_LOG_DIR_PATH', '/var/log/OneSilaHeadless/magento')


#
# Shopify integration Settings (sales_channels.integrations.shopify)
#

SHOPIFY_SCOPES = ['read_products', 'write_products', 'read_locales', 'read_orders', 'read_publications', 'write_publications']
SHOPIFY_API_VERSION = "2025-04"
SHOPIFY_TEST_REDIRECT_URI = os.getenv('SHOPIFY_TEST_REDIRECT_URI')
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_SECRET = os.getenv('SHOPIFY_API_SECRET')
#
# OpenAI settings. (llm)
#

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
AI_POINT_PRICE = os.getenv('AI_POINT_PRICE', 0.1)

#
# Telegram settings. (notifications)
#

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        # The amazon package has a bug that shows you a log of the
        # request x-times every time you do a request.
        # This stops that flood to ensure we can actually use logs
        # without loosing track.
        # Keep both http.client + urllib3.connectinpool + requests.packages.urllib3.connectionpool
        # to ensure we cover all bases.
        'http.client': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # optional redundancy
        'requests.packages.urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        # 'file': {
        #     'level': 'DEBUG',
        #     'class': 'logging.FileHandler',
        #     'filename': '/var/log/OneSilaHeadless/django.log',
        #     'formatter': 'verbose',
        # },
    },
    # The amazon package has a bug that shows you a log of the
    # request x-times every time you do a request. The 'root' logger
    # config is for the same purpose of the remarks above in 'loggers'
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
