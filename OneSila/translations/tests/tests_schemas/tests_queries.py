from django.test import TestCase, TransactionTestCase
from translations.models import TranslationFieldsMixin
from translations.schema.types.types import TranslationLanguageType

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin

class TranslationsQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_translation_languages(self):
        query = """
            query translationLanguages {
              translationLanguages {
                code
                name
              }
            }
        """

        resp = self.stawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        expected_languages = [TranslationLanguageType(code=code, name=name) for code, name in TranslationFieldsMixin.LANGUAGES.ALL]
        received_languages = resp.data['translationLanguages']

        self.assertEqual(len(received_languages), len(expected_languages))
        for received_language, expected_language in zip(received_languages, expected_languages):
            self.assertEqual(received_language['code'], expected_language.code)
            self.assertEqual(received_language['name'], expected_language.name)
