from django.test import TestCase, TransactionTestCase
from translations.models import TranslationFieldsMixin
from translations.schema.types.types import TranslationLanguageType

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class TranslationsQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_translation_languages(self):
        query = """
            query translationLanguages {
              translationLanguages {
                languages {
                  code
                  name
                }
                defaultLanguage {
                  code
                  name
                }
              }
            }
        """

        resp = self.strawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        # Prepare expected results
        expected_languages = [
            TranslationLanguageType(code=code, name=name)
            for code, name in TranslationFieldsMixin.LANGUAGES
        ]

        default_language_code = "en"
        default_language_name = dict(TranslationFieldsMixin.LANGUAGES).get(default_language_code, "Unknown")
        expected_default_language = TranslationLanguageType(code=default_language_code, name=default_language_name)

        received_data = resp.data['translationLanguages']
        received_languages = received_data['languages']
        received_default_language = received_data['defaultLanguage']

        # Check the list of languages
        self.assertEqual(len(received_languages), len(expected_languages))
        for received_language, expected_language in zip(received_languages, expected_languages):
            self.assertEqual(received_language['code'], expected_language.code)
            self.assertEqual(received_language['name'], expected_language.name)

        # Check the default language
        self.assertEqual(received_default_language['code'], expected_default_language.code)
        self.assertEqual(received_default_language['name'], expected_default_language.name)
