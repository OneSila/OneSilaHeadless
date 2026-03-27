from django.test import TransactionTestCase
from model_bakery import baker

from core.models import MultiTenantCompany
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from eancodes.models import EanCode
from products.models import SimpleProduct


MANUAL_ASSIGN_EAN_CODE_MUTATION = """
    mutation($data: ManualAssignEancodeInput!) {
      manualAssignEanCode(data: $data) {
        id
        eanCode
        product {
          id
        }
      }
    }
"""


class ManualAssignEanCodeMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

    def _mutation_variables(self, *, product, ean_code):
        return {
            "data": {
                "product": {"id": self.to_global_id(product)},
                "eanCode": {"id": self.to_global_id(ean_code)},
            }
        }

    def _assert_graphql_error_contains(self, *, response, text):
        self.assertTrue(response.errors)
        self.assertIn(text, response.errors[0].message)

    def test_manual_assign_ean_code(self):
        ean_code = EanCode.objects.create(
            ean_code="1234567890123",
            internal=True,
            already_used=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=ean_code),
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["manualAssignEanCode"]
        self.assertEqual(payload["id"], self.to_global_id(ean_code))
        self.assertEqual(payload["eanCode"], ean_code.ean_code)
        self.assertEqual(payload["product"]["id"], self.to_global_id(self.product))

        ean_code.refresh_from_db()
        self.assertEqual(ean_code.product_id, self.product.id)

    def test_manual_assign_ean_code_rejects_used_ean_code(self):
        ean_code = EanCode.objects.create(
            ean_code="1234567890124",
            internal=False,
            already_used=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="already been used")
        ean_code.refresh_from_db()
        self.assertIsNone(ean_code.product_id)

    def test_manual_assign_ean_code_rejects_non_internal_ean_code(self):
        ean_code = EanCode.objects.create(
            ean_code="1234567890125",
            internal=False,
            already_used=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="Only internal EAN codes can be manually assigned")
        ean_code.refresh_from_db()
        self.assertIsNone(ean_code.product_id)

    def test_manual_assign_ean_code_rejects_product_with_existing_ean_code(self):
        EanCode.objects.create(
            ean_code="1234567890126",
            internal=True,
            already_used=False,
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
        )
        new_ean_code = EanCode.objects.create(
            ean_code="1234567890127",
            internal=True,
            already_used=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=new_ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="already has an EAN code assigned")
        new_ean_code.refresh_from_db()
        self.assertIsNone(new_ean_code.product_id)

    def test_manual_assign_ean_code_rejects_ean_code_from_another_company(self):
        other_company = baker.make(MultiTenantCompany)
        other_ean_code = EanCode.objects.create(
            ean_code="1234567890128",
            internal=True,
            already_used=False,
            multi_tenant_company=other_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=other_ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="valid EAN code")
        other_ean_code.refresh_from_db()
        self.assertIsNone(other_ean_code.product_id)

    def test_manual_assign_ean_code_rejects_product_from_another_company(self):
        other_company = baker.make(MultiTenantCompany)
        other_product = SimpleProduct.objects.create(multi_tenant_company=other_company)
        ean_code = EanCode.objects.create(
            ean_code="1234567890129",
            internal=True,
            already_used=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=other_product, ean_code=ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="valid product")
        ean_code.refresh_from_db()
        self.assertIsNone(ean_code.product_id)

    def test_manual_assign_ean_code_rejects_ean_code_already_assigned_to_another_product(self):
        other_product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ean_code = EanCode.objects.create(
            ean_code="1234567890130",
            internal=True,
            already_used=False,
            product=other_product,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=MANUAL_ASSIGN_EAN_CODE_MUTATION,
            variables=self._mutation_variables(product=self.product, ean_code=ean_code),
            asserts_errors=False,
        )

        self._assert_graphql_error_contains(response=resp, text="already assigned to another product")
        ean_code.refresh_from_db()
        self.assertEqual(ean_code.product_id, other_product.id)
