from django.core.exceptions import ValidationError
from llm.factories.translations import StringTranslationLLM
from llm.schema.types.input import ContentAiGenerateType
from django.utils.translation import gettext_lazy as _
from products.models import Product, ProductTranslation
from properties.models import Property, PropertySelectValue, PropertyTranslation, PropertySelectValueTranslation


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

    def _get_safe_translation(self, translation, attr):
        """Helper method to safely get a translation attribute."""
        return getattr(translation, attr, '') or ''

    def _set_product_translation(self):
        if self.product:
            translation = self.product.translations.exclude(language=self.to_language_code).first()

            if translation:
                if self.content_type == ContentAiGenerateType.DESCRIPTION:
                    self.to_translate = self._get_safe_translation(translation, 'description')

                if self.content_type == ContentAiGenerateType.SHORT_DESCRIPTION:
                    self.to_translate = self._get_safe_translation(translation, 'short_description')

                if self.content_type == ContentAiGenerateType.NAME:
                    self.to_translate = self._get_safe_translation(translation, 'name')

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


class BulkAiTranslateContentFlow:
    def __init__(self, multi_tenant_company, from_language_code: str, to_language_codes: list[str], products=None, properties=None, values=None, override_translation: bool = False,):
        self.multi_tenant_company = multi_tenant_company
        self.from_language_code = from_language_code
        self.to_language_codes = to_language_codes
        self.products = products or Product.objects.none()
        self.properties = properties or Property.objects.none()
        self.values = values or PropertySelectValue.objects.none()
        self.total_points = 0
        self.override_translation = override_translation

    def translate_products(self):

        for product in self.products.iterator():
            for to_lang in self.to_language_codes:
                translation, created = ProductTranslation.objects.get_or_create(
                    product=product,
                    language=to_lang,
                    multi_tenant_company=self.multi_tenant_company
                )

                updated = False

                for content_type in [
                    ContentAiGenerateType.NAME,
                    ContentAiGenerateType.SHORT_DESCRIPTION,
                    ContentAiGenerateType.DESCRIPTION
                ]:
                    try:
                        field_name = content_type.value
                        existing_value = getattr(translation, field_name, None)

                        if existing_value == '<p><br></p>':
                            existing_value = None

                        # Check if we should skip based on override flag
                        if not created and existing_value and not self.override_translation:
                            continue

                        flow = AITranslateContentFlow(
                            to_translate=None,
                            from_language_code=self.from_language_code,
                            to_language_code=to_lang,
                            multi_tenant_company=self.multi_tenant_company,
                            product=product,
                            content_type=content_type
                        )
                        flow.flow()

                        setattr(translation, field_name, flow.translated_content)
                        self.total_points += flow.used_points
                        updated = True

                    except Exception:
                        pass

                if updated:
                    translation.save()

    def _translate_generic_entities(
            self,
            queryset,
            field_name: str,
            related_name: str,
            translation_model,
            get_or_create_field: str,
            assign_field: str
    ):
        for obj in queryset.iterator():
            original_value = obj._get_translated_value(
                field_name=field_name,
                related_name=related_name,
                language=self.from_language_code
            )

            if not original_value or original_value.strip() == "":
                continue

            for to_lang in self.to_language_codes:

                try:
                    flow = AITranslateContentFlow(
                        to_translate=original_value,
                        from_language_code=self.from_language_code,
                        to_language_code=to_lang,
                        multi_tenant_company=self.multi_tenant_company
                    )
                    flow.flow()

                    translation, created = translation_model.objects.get_or_create(
                        **{get_or_create_field: obj, "language": to_lang,
                           "multi_tenant_company": self.multi_tenant_company}
                    )

                    # Skip if existing value and not overriding
                    existing_value = getattr(translation, assign_field, None)
                    if not created and existing_value and not self.override_translation:
                        continue


                    setattr(translation, assign_field, flow.translated_content)
                    translation.save()

                    self.total_points += flow.used_points

                except Exception:
                    pass


    def translate_properties(self):

        self._translate_generic_entities(
            queryset=self.properties,
            field_name='name',
            related_name='propertytranslation_set',
            translation_model=PropertyTranslation,
            get_or_create_field='property',
            assign_field='name'
        )


    def translate_values(self):

        self._translate_generic_entities(
            queryset=self.values,
            field_name='value',
            related_name='propertyselectvaluetranslation_set',
            translation_model=PropertySelectValueTranslation,
            get_or_create_field='propertyselectvalue',
            assign_field='value'
        )


    def run(self):
        self.translate_products()
        self.translate_properties()
        self.translate_values()