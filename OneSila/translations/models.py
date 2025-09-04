from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

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

    language = models.CharField(max_length=7, choices=LANGUAGES, default=settings.LANGUAGE_CODE, db_index=True)

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
    def _get_translated_value(self, *, field_name, language=None, related_name='translations', fallback=None, sales_channel=None):
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

        is_sales_channel_translation = False
        translation_kwargs = {
            'language': language,
        }

        if related_name == 'translations': # is a product translation
            translation_kwargs['sales_channel'] = sales_channel

        try:
            translation = translations.get(**translation_kwargs)

            if sales_channel is not None and related_name == 'translations':
                is_sales_channel_translation = True

        except ObjectDoesNotExist:

            # If we were searching by sales_channel, try again without it (default)
            if related_name == 'translations' and sales_channel is not None:

                # Try to get translation just by language
                try:
                    translation = translations.get(language=language, sales_channel=None)
                except ObjectDoesNotExist:
                    translation = translations.last()
            else:
                translation = translations.last()

        if translation:
            translated_value = getattr(translation, field_name, '')

        if translated_value == ''  and is_sales_channel_translation and related_name == 'translations' and sales_channel is not None:

            # if the translation instance WAS found but the field doesn't have a value for example there is no description
            # we will use the default one to populate it
            return self._get_translated_value(
                field_name=field_name,
                language=language,
                related_name=related_name,
                fallback=fallback,
                sales_channel=None
            )

        return translated_value

    class Meta:
        abstract = True
