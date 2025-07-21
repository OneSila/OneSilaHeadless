from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertyTranslation


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
