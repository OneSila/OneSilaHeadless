from django.apps import AppConfig

import django.db.models.options as options
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'translated_field',)


class TranslationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'translations'

    def ready(self):
        from . import receivers
