from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from .tests_schemas.queries import (
    PROPERTIES_MISSING_MAIN_TRANSLATION_QUERY,
    PROPERTIES_MISSING_TRANSLATIONS_QUERY,
    PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATION_QUERY,
    PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY,
)


class PropertyFilterTranslationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.languages = ["en", "fr"]
        self.multi_tenant_company.save()
        self.p1 = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            property=self.p1,
            language="en",
            name="Color",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.p2 = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            property=self.p2,
            language="en",
            name="Size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=self.p2,
            language="fr",
            name="Taille",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.p3 = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            property=self.p3,
            language="fr",
            name="Poids",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, query, variables):
        resp = self.strawberry_test_client(query=query, variables=variables)
        self.assertIsNone(resp.errors)
        expected_ids = {self.p1.id, self.p2.id, self.p3.id}

        found_ids = {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["properties"]["edges"]
        }

        return found_ids & expected_ids

    def test_property_missing_main_translation_true(self):
        ids = self._query_ids(
            PROPERTIES_MISSING_MAIN_TRANSLATION_QUERY,
            {"missingMainTranslation": True},
        )
        self.assertSetEqual(ids, {self.p3.id})

    def test_property_missing_main_translation_false(self):
        ids = self._query_ids(
            PROPERTIES_MISSING_MAIN_TRANSLATION_QUERY,
            {"missingMainTranslation": False},
        )
        self.assertSetEqual(ids, {self.p1.id, self.p2.id})

    def test_property_missing_translations_true(self):
        ids = self._query_ids(
            PROPERTIES_MISSING_TRANSLATIONS_QUERY,
            {"missingTranslations": True},
        )
        self.assertSetEqual(ids, {self.p1.id, self.p3.id})

    def test_property_missing_translations_false(self):
        ids = self._query_ids(
            PROPERTIES_MISSING_TRANSLATIONS_QUERY,
            {"missingTranslations": False},
        )
        self.assertSetEqual(ids, {self.p2.id})


class PropertySelectValueFilterTranslationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.languages = ["en", "fr"]
        self.multi_tenant_company.save()
        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            property=self.property,
            language="en",
            name="Color",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=self.property,
            language="fr",
            name="Couleur",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.v1 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.v1,
            language="en",
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.v2 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.v2,
            language="en",
            value="Green",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.v2,
            language="fr",
            value="Vert",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.v3 = PropertySelectValue.objects.create(
            property=self.property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.v3,
            language="fr",
            value="Bleu",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, query, variables):
        resp = self.strawberry_test_client(query=query, variables=variables)
        self.assertIsNone(resp.errors)
        return {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["propertySelectValues"]["edges"]
        }

    def test_property_select_value_missing_main_translation_true(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATION_QUERY,
            {"missingMainTranslation": True},
        )
        self.assertSetEqual(ids, {self.v3.id})

    def test_property_select_value_missing_main_translation_false(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATION_QUERY,
            {"missingMainTranslation": False},
        )
        self.assertSetEqual(ids, {self.v1.id, self.v2.id})

    def test_property_select_value_missing_translations_true(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY,
            {"missingTranslations": True},
        )
        self.assertSetEqual(ids, {self.v1.id, self.v3.id})

    def test_property_select_value_missing_translations_false(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY,
            {"missingTranslations": False},
        )
        self.assertSetEqual(ids, {self.v2.id})
