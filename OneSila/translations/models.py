from core import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.helpers import get_languages


class TranslationFieldsMixin(models.Model):
    """
    Languages we can translate content into.
    """
    LANGUAGES = get_languages()

    language = models.CharField(max_length=7, choices=LANGUAGES, default=settings.LANGUAGE_CODE)

    class Meta:
        abstract = True
