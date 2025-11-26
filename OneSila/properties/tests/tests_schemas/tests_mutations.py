from django.test import TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import (
    ProductProperty,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from products.models import Product


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


class MergePropertySelectValueMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
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
        self.value1 = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.value2 = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.target = PropertySelectValue.objects.create(
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.value1,
            language=self.multi_tenant_company.language,
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.value2,
            language=self.multi_tenant_company.language,
            value="Blue",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.prop,
            multi_tenant_company=self.multi_tenant_company,
            value_select=self.value1,
        )

        # @TODO: Come later! M2m does't work
        #self.product_property.value_multi_select.add(self.value1, self.value2)

    def test_merge_property_select_value(self):
        mutation = """
            mutation($sources: [PropertySelectValuePartialInput!]!, $target: PropertySelectValuePartialInput!) {
              mergePropertySelectValue(sources: $sources, target: $target) { id }
            }
        """
        variables = {
            "sources": [
                {"id": self.to_global_id(self.value1)},
                {"id": self.to_global_id(self.value2)},
            ],
            "target": {"id": self.to_global_id(self.target)},
        }
        resp = self.strawberry_test_client(query=mutation, variables=variables)

        self.assertIsNone(resp.errors)
        self.assertEqual(
            resp.data["mergePropertySelectValue"]["id"],
            self.to_global_id(self.target),
        )
        self.assertFalse(
            PropertySelectValue.objects.filter(id__in=[self.value1.id, self.value2.id]).exists()
        )
        self.product_property.refresh_from_db()
        self.assertEqual(self.product_property.value_select_id, self.target.id)
        # self.assertListEqual(list(self.product_property.value_multi_select.all()), [self.target])


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
            variables={"property": {"id": self.to_global_id(self.prop)}, "value": "Redd"},
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
