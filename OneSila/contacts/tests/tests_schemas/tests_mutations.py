from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class CompanyQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_company(self):

        mutation = """
            mutation createCompany($name: String!) {
                createCompany(data: {name: $name}) {
                    id
                    name
                }
            }
        """

        company_name = 'test_company'

        resp = schema.execute_sync(
            query=mutation,
            context_value=self.context,
            variable_values={"name": company_name},
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['createCompany']['name']

        self.assertEqual(resp_company_name, company_name)


class SupplierQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_supplier(self):

        mutation = """
            mutation createSupplier($name: String!) {
                createSupplier(data: {name: $name}) {
                    id
                    name
                }
            }
        """

        company_name = 'test_supplier'

        resp = schema.execute_sync(
            query=mutation,
            context_value=self.context,
            variable_values={"name": company_name},
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_company_name = resp.data['createSupplier']['name']

        self.assertEqual(resp_company_name, company_name)
