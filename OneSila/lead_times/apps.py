from django.apps import AppConfig


class LeadTimesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lead_times'


def ready(self):
    from . import receivers
