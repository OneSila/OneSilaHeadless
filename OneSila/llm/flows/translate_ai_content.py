from django.core.exceptions import ValidationError
from llm.factories.translations import StringTranslationLLM
from llm.schema.types.input import ContentAiGenerateType
from django.utils.translation import gettext_lazy as _


class AITranslateContentFlow:
    def __init__(self, to_translate, from_language_code, to_language_code, multi_tenant_company, product=None, content_type=None):
        self.to_translate = to_translate
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.multi_tenant_company = multi_tenant_company
        self.product = product
        self.content_type = content_type
        self.translated_content = ''
        self.used_points = 0

    def _set_product_translation(self):
        if self.product:
            translation = self.product.translations.exclude(language=self.to_language_code).first()

            if translation:
                if self.content_type == ContentAiGenerateType.DESCRIPTION:
                    self.to_translate = translation.description

                if self.content_type == ContentAiGenerateType.SHORT_DESCRIPTION:
                    self.to_translate = translation.short_description

                if self.content_type == ContentAiGenerateType.NAME:
                    self.to_translate = translation.name

                self.from_language_code = translation.language

    def _validate(self):
        if self.to_translate == '' or self.to_translate == '<p><br></p>':
            raise ValidationError(_("There is no source to translate"))

    def _set_factory(self):
        self.factory = StringTranslationLLM(
            to_translate=self.to_translate,
            from_language_code=self.from_language_code,
            to_language_code=self.to_language_code,
             multi_tenant_company=self.multi_tenant_company)

    def translate_content(self):
        translated_str = self.factory.translate()
        process = self.factory.ai_process

        self.translated_content = translated_str
        self.used_points = process.transaction.points

    def flow(self):
        self._set_product_translation()
        self._set_factory()
        self._validate()
        self.translate_content()
        return self.translated_content