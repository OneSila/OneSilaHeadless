from django.test import SimpleTestCase

from core.locales import normalize_language_code, normalize_language_list


class LocaleNormalizationTests(SimpleTestCase):
    def test_normalize_legacy_language_code(self):
        self.assertEqual(normalize_language_code(code="en"), "en-gb")
        self.assertEqual(normalize_language_code(code="fr"), "fr-fr")

    def test_normalize_language_aliases(self):
        self.assertEqual(normalize_language_code(code="en-gb"), "en-gb")
        self.assertEqual(normalize_language_code(code="pt-br"), "pt-br")
        self.assertEqual(normalize_language_code(code="zh-hans"), "zh-cn")

    def test_normalize_language_list_deduplicates(self):
        self.assertEqual(
            normalize_language_list(values=["en", "en-gb", "fr", "fr-fr"]),
            ["en-gb", "fr-fr"],
        )
