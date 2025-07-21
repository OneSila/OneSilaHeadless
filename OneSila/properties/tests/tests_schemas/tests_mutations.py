from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation


class CheckPropertyForDuplicatesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()

        self.prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        PropertyTranslation.objects.create(
            property=self.prop,
            language=self.multi_tenant_company.language,
            name="Color",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_duplicate_found(self):
        mutation = """
            mutation($name: String!) {
              checkPropertyForDuplicates(name: $name) {
                duplicateFound
                duplicates { id }
              }
            }
        """
        resp = self.strawberry_test_client(query=mutation, variables={"name": "Color"})

        self.assertIsNone(resp.errors)
        data = resp.data["checkPropertyForDuplicates"]
        self.assertTrue(data["duplicateFound"])
        self.assertEqual(len(data["duplicates"]), 1)

    def test_no_duplicate_found(self):
        mutation = """
            mutation($name: String!) {
              checkPropertyForDuplicates(name: $name) {
                duplicateFound
                duplicates { id }
              }
            }
        """
        resp = self.strawberry_test_client(query=mutation, variables={"name": "Weight"})

        self.assertIsNone(resp.errors)
        data = resp.data["checkPropertyForDuplicates"]
        self.assertFalse(data["duplicateFound"])
        self.assertEqual(len(data["duplicates"]), 0)


class CheckPropertySelectValueForDuplicatesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()

        self.prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            property=self.prop,
            language=self.multi_tenant_company.language,
            name="Color",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.select_value = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.select_value,
            language=self.multi_tenant_company.language,
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_duplicate_found(self):
        mutation = """
            mutation($property: PropertyPartialInput!, $value: String!) {
              checkPropertySelectValueForDuplicates(property: $property, value: $value) {
                duplicateFound
                duplicates { id }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"property": {"id": self.to_global_id(self.prop)}, "value": "Red2"},
        )

        self.assertIsNone(resp.errors)
        data = resp.data["checkPropertySelectValueForDuplicates"]
        self.assertTrue(data["duplicateFound"])
        self.assertEqual(len(data["duplicates"]), 1)

    def test_no_duplicate_found(self):
        mutation = """
            mutation($property: PropertyPartialInput!, $value: String!) {
              checkPropertySelectValueForDuplicates(property: $property, value: $value) {
                duplicateFound
                duplicates { id }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"property": {"id": self.to_global_id(self.prop)}, "value": "Blue"},
        )

        self.assertIsNone(resp.errors)
        data = resp.data["checkPropertySelectValueForDuplicates"]
        self.assertFalse(data["duplicateFound"])
        self.assertEqual(len(data["duplicates"]), 0)
