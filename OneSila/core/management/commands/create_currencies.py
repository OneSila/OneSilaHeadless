from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.urls import URLPattern, URLResolver

class Command(BaseCommand):
    help = 'Create basic currencies.'

    def handle(self, *args, **options):
        from currencies.currencies import currencies
        from currencies.models import PublicCurrency

        for key, item in currencies.items():
            PublicCurrency.objects.get_or_create(**item)