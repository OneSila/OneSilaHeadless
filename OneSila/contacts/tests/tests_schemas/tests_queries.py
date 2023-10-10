from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class CompanyQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.companies = baker.make(Company, multi_tenant_company=self.user.multi_tenant_company, _quantity=3)

    def test_companies(self):
        query = """
            query companies {
              companies {
                edges {
                  node {
                    id
                  }
                }
                totalCount
              }
            }
        """

        resp = self.stawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        total_count = resp.data['companies']['totalCount']
        self.assertEqual(total_count, len(self.companies))

    def test_company(self):
        query = """
            query company($id: GlobalID!) {
                company(id: $id) {
                    id
                    name
                }
            }
        """
        company = self.companies[0]
        company_global_id = self.to_global_id(model_class=Company, instance_id=company.id)
        resp = self.stawberry_test_client(
            query=query,
            variables={"id": company_global_id}
        )
        resp_company_name = resp.data['company']['name']
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp_company_name, company.name)


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
        resp = self.stawberry_test_client(
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
                }
            }
        """
        supplier = self.suppliers[0]
        supplier_global_id = self.to_global_id(model_class=Supplier, instance_id=supplier.id)
        resp = self.stawberry_test_client(
            query=query,
            variables={"id": supplier_global_id}
        )
        resp_supplier_name = resp.data['supplier']['name']
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp_supplier_name, supplier.name)
