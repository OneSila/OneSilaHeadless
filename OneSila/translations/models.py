from core import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class TranslationFieldsMixin(models.Model):
    """
    Languages we can translate content into.
    """
    class LANGUAGES:
        DUTCH = 'NL'
        ENGLISH = 'EN'

        ALL = (
            (DUTCH, _("Dutch")),
            (ENGLISH, _("English"))
        )

    language = models.CharField(max_length=5, choices=LANGUAGES.ALL)

    class Meta:
        abstract = True
