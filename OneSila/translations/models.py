from django.core.exceptions import ObjectDoesNotExist

from core import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.helpers import get_languages
from django.db.models import Model as OldModel


class TranslationFieldsMixin(models.Model):
    """
    Languages we can translate content into.
    """
    LANGUAGES = get_languages()

    language = models.CharField(max_length=7, choices=LANGUAGES, default=settings.LANGUAGE_CODE)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # if we have translated field on the meta on the model we auto populate the multi tenant company from it. Is very easy to forget that
        # the translation models also have multi tenant company

        if not hasattr(self, 'multi_tenant_company') or self.multi_tenant_company is None:
            translated_field = getattr(self._meta, 'translated_field', None)
            if translated_field:
                related_object = getattr(self, translated_field, None)
                if related_object and hasattr(related_object, 'multi_tenant_company'):
                    self.multi_tenant_company = related_object.multi_tenant_company

        super().save(*args, **kwargs)


class TranslatedModelMixin(OldModel):
    def _get_translated_value(self, *, field_name, language=None, related_name='translations', fallback=None):
        # we use '' (empty string) instead of None here because some of the translated values severs as __str__
        # __str__ can't be None. In the same process we also create the translation but if we have __str__ None then the process will not work
        translated_value = ''
        if fallback is not None:
            translated_value = fallback

        translations = getattr(self, related_name).all()
        if not translations:
            return translated_value

        if language is None:
            multi_tenant_company = getattr(self, 'multi_tenant_company', None)
            language = multi_tenant_company.language

        try:
            translation = translations.get(language=language)
        except ObjectDoesNotExist:
            translation = translations.last()

        if translation:
            translated_value = getattr(translation, field_name, '')

        return translated_value

    class Meta:
        abstract = True
