from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress
from contacts.schema.types.types import SupplierType, CompanyType, CustomerType

from core.tests import TestCaseWithDemoData
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class AddressTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.addresses = Address.objects.filter(multi_tenant_company=self.user.multi_tenant_company)

    def test_addresses(self):
        from .queries import ADDRESS_QUERY

        resp = self.strawberry_test_client(
            query=ADDRESS_QUERY,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        total_count = resp.data['addresses']['totalCount']
        self.assertEqual(total_count, len(self.addresses))


class CompanyQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.companies = baker.make(Company, multi_tenant_company=self.user.multi_tenant_company, _quantity=3)

    def test_companies(self):
        from .queries import COMPANIES_QUERY

        resp = self.strawberry_test_client(
            query=COMPANIES_QUERY,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        total_count = resp.data['companies']['totalCount']
        self.assertEqual(total_count, len(self.companies))

    def test_company_list_filter_frontend_page(self):
        from .queries import COMPANY_LIST_FILTER_FRONTEND
        query_filter = {"isInternalCompany": {"exact": False}}
        resp = self.strawberry_test_client(
            query=COMPANY_LIST_FILTER_FRONTEND,
            variables={
                'filter': query_filter,
            }
        )

        self.assertTrue(resp.errors is None)

    def test_company(self):
        from .queries import COMPANY_GET_QUERY
        company = self.companies[0]
        company_global_id = self.to_global_id(instance=company)
        resp = self.strawberry_test_client(
            query=COMPANY_GET_QUERY,
            variables={"id": company_global_id}
        )
        resp_company_name = resp.data['company']['name']
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp_company_name, company.name)

        typename = resp.data['company']['__typename']

        self.assertEqual(typename, CompanyType.__name__)


class SupplierQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.suppliers = baker.make(Supplier, multi_tenant_company=self.user.multi_tenant_company, is_supplier=True, _quantity=3)
        # Lets make sure they are correctly filtered - create some non suppliers.
        self.companies = baker.make(Company, multi_tenant_company=self.user.multi_tenant_company, is_supplier=False, _quantity=3)

    def test_suppliers(self):
        query = """
            query suppliers {
              suppliers {
                edges {
                  node {
                    id
                  }
                }
                totalCount
              }
            }
        """

        # resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"})
        resp = self.strawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        total_count = resp.data['suppliers']['totalCount']
        self.assertEqual(total_count, len(self.suppliers))

    def test_supplier(self):
        query = """
            query supplier($id: GlobalID!) {
                supplier(id: $id) {
                    id
                    name
                    __typename
                }
            }
        """
        supplier = self.suppliers[0]
        supplier_global_id = self.to_global_id(instance=supplier)
        resp = self.strawberry_test_client(
            query=query,
            variables={"id": supplier_global_id}
        )
        resp_supplier_name = resp.data['supplier']['name']
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp_supplier_name, supplier.name)

        typename = resp.data['supplier']['__typename']
        self.assertEqual(typename, SupplierType.__name__)


class CustomerQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.customers = baker.make(Customer, multi_tenant_company=self.user.multi_tenant_company, is_customer=True, _quantity=3)
        # Lets make sure they are correctly filtered - create some non suppliers.
        self.companies = baker.make(Company, multi_tenant_company=self.user.multi_tenant_company, is_supplier=False, _quantity=3)

    def test_customers(self):
        query = """
            query customers {
              customers {
                edges {
                  node {
                    id
                  }
                }
                totalCount
              }
            }
        """

        # resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"})
        resp = self.strawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        total_count = resp.data['customers']['totalCount']
        self.assertEqual(total_count, len(self.customers))

    def test_customer(self):
        query = """
            query customer($id: GlobalID!) {
                customer(id: $id) {
                    id
                    name
                    __typename
                    isCustomer
                }
            }
        """
        customer = self.customers[0]
        customer_global_id = self.to_global_id(instance=customer)
        resp = self.strawberry_test_client(
            query=query,
            variables={"id": customer_global_id}
        )
        resp_customer_name = resp.data['customer']['name']
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp_customer_name, customer.name)

        typename = resp.data['customer']['__typename']
        self.assertEqual(typename, CustomerType.__name__)

        self.assertTrue(resp.data['customer']['isCustomer'])
