from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
)
from products.models import SimpleProduct
from .tests_schemas.queries import (
    PROPERTIES_MISSING_MAIN_TRANSLATION_QUERY,
    PROPERTIES_MISSING_TRANSLATIONS_QUERY,
    PROPERTIES_USED_IN_PRODUCTS_QUERY,
    PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATION_QUERY,
    PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY,
    PROPERTY_SELECT_VALUES_USED_IN_PRODUCTS_QUERY,
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


class PropertyFilterUsedInProductsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.p_used = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.p_unused = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        ProductProperty.objects.create(
            product=product,
            property=self.p_used,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, query, variables):
        resp = self.strawberry_test_client(query=query, variables=variables)
        self.assertIsNone(resp.errors)
        return {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["properties"]["edges"]
        }

    def test_property_used_in_products_true(self):
        ids = self._query_ids(
            PROPERTIES_USED_IN_PRODUCTS_QUERY,
            {"usedInProducts": True},
        )
        self.assertSetEqual(ids, {self.p_used.id})


class PropertySelectValueFilterUsedInProductsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.prop_select = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.prop_multi = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.MULTISELECT,
        )
        self.v_select_used = PropertySelectValue.objects.create(
            property=self.prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.v_select_unused = PropertySelectValue.objects.create(
            property=self.prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.v_multi_used = PropertySelectValue.objects.create(
            property=self.prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        ProductProperty.objects.create(
            product=product,
            property=self.prop_select,
            value_select=self.v_select_used,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi = ProductProperty.objects.create(
            product=product,
            property=self.prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi.value_multi_select.set([self.v_multi_used])

    def _query_ids(self, query, variables):
        resp = self.strawberry_test_client(query=query, variables=variables)
        self.assertIsNone(resp.errors)
        return {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["propertySelectValues"]["edges"]
        }

    def test_property_select_value_used_in_products_true(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_USED_IN_PRODUCTS_QUERY,
            {"usedInProducts": True},
        )
        self.assertSetEqual(ids, {self.v_select_used.id, self.v_multi_used.id})

    def test_property_select_value_used_in_products_false(self):
        ids = self._query_ids(
            PROPERTY_SELECT_VALUES_USED_IN_PRODUCTS_QUERY,
            {"usedInProducts": False},
        )
        self.assertSetEqual(ids, {self.v_select_unused.id})
