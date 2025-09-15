from django.apps import AppConfig

# We added a search_terms settting to all managers.
# One the Meta Fields, we should set this.
import django.db.models.options as options
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'search_terms',)

# We added a url_detail_page_string setting to all models.
# One the Meta Fields, we should set this.
options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, 'url_detail_page_string',)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from . import receivers
