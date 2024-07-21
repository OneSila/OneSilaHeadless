from django.apps import AppConfig

# We added a search_terms settting to all managers.
# One the Meta Fields, we should set this.
import django.db.models.options as options
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'search_terms',)
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'translated_field',)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from . import receivers
