from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class CompanyQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_company_create(self):
        mutation = """
            mutation createCompany($name: String!) {
                createCompany(data: {name: $name}) {
                    id
                    name
                }
            }
        """

        company_name = 'test_company_create'

        resp = self.strawberry_test_client(
            query=mutation,
            variables={"name": company_name}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['createCompany']['name']

        self.assertEqual(resp_company_name, company_name)

    def test_company_update(self):
        mutation = """
            mutation updateCompany($id: GlobalID!, $name: String!) {
                updateCompany(data: {id: $id, name: $name}) {
                    id
                    name
                }
            }
        """
        company = Company.objects.create(name='test_company_update_ori', multi_tenant_company=self.multi_tenant_company)
        company_global_id = self.to_global_id(instance=company)
        company_name = 'test_company_update'

        resp = self.strawberry_test_client(
            query=mutation,
            variables={"id": company_global_id, "name": company_name}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['updateCompany']['name']

        self.assertEqual(resp_company_name, company_name)


class SupplierQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_supplier_create(self):
        mutation = """
            mutation createSupplier($name: String!) {
                createSupplier(data: {name: $name}) {
                    id
                    name
                }
            }
        """
        company_name = 'test_supplier'

        resp = self.strawberry_test_client(
            query=mutation,
            variables={"name": company_name}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['createSupplier']['name']

        self.assertEqual(resp_company_name, company_name)

    def test_supplier_update(self):
        mutation = """
            mutation updateSupplier($id: GlobalID!, $name: String!) {
                updateSupplier(data: {id: $id, name: $name}) {
                    id
                    name
                }
            }
        """
        company = Supplier.objects.create(name='test_supplier_update_ori', multi_tenant_company=self.multi_tenant_company)
        company_global_id = self.to_global_id(instance=company)
        company_name = 'test_supplier_update'

        resp = self.strawberry_test_client(
            query=mutation,
            variables={"name": company_name, "id": company_global_id},
            asserts_errors=False,

        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['updateSupplier']['name']

        self.assertEqual(resp_company_name, company_name)

    def test_company_to_supplier_update(self):
        mutation = """
            mutation updateSupplier($id: GlobalID!, $name: String!) {
                updateSupplier(data: {id: $id, name: $name}) {
                    id
                    name
                }
            }
        """
        company = Supplier.objects.create(name='test_company_to_supplier_update_ori', multi_tenant_company=self.multi_tenant_company)
        # company.is_supplier = True
        # company.save()

        company_global_id = self.to_global_id(instance=company)
        company_name = 'test_company_to_supplier_update'

        resp = self.strawberry_test_client(
            query=mutation,
            variables={"name": company_name, "id": company_global_id},
            asserts_errors=False,
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['updateSupplier']['name']

        self.assertEqual(resp_company_name, company_name)
