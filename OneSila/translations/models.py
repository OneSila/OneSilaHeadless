from core import models
from django.conf import settings


class TranslationFieldsMixin(models.Model):
    LANGUAGE_CHOICES = settings.LANGUAGES
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)

    class Meta:
        abstract = True
