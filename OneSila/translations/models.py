from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin
from django.conf import settings


class TranslationFieldsMixin(MultiTenantAwareMixin, models.Model):
    LANGUAGE_CHOICES = settings.LANGUAGES
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)

    class Meta:
        abstract = True
