from django.test import TransactionTestCase
from model_bakery import baker

from core.models import MultiTenantCompany
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from media.models import DocumentType


class DocumentTypeQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.document_type = DocumentType.objects.create(
            name="Kid Certificate",
            description="Safety document for child products",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_document_type_node_query(self):
        query = """
            query ($id: GlobalID!) {
              documentType(id: $id) {
                id
                name
                code
                description
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"id": self.to_global_id(self.document_type)},
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(resp.data["documentType"]["id"], self.to_global_id(self.document_type))
        self.assertEqual(resp.data["documentType"]["name"], "Kid Certificate")
        self.assertEqual(resp.data["documentType"]["code"], "KID_CERTIFICATE")
        self.assertEqual(resp.data["documentType"]["description"], "Safety document for child products")

    def test_document_types_search_by_name_code_and_description(self):
        DocumentType.objects.create(
            name="Company Certificate",
            description="Certificates used at company level",
            multi_tenant_company=self.multi_tenant_company,
        )

        query = """
            query ($search: String!) {
              documentTypes(filters: {search: $search}) {
                edges {
                  node {
                    id
                    name
                    code
                  }
                }
              }
            }
        """

        by_name = self.strawberry_test_client(query=query, variables={"search": "Kid"})
        by_code = self.strawberry_test_client(query=query, variables={"search": "KID_CERTIFICATE"})
        by_description = self.strawberry_test_client(
            query=query,
            variables={"search": "child products"},
        )

        self.assertIsNone(by_name.errors)
        self.assertIsNone(by_code.errors)
        self.assertIsNone(by_description.errors)

        for response in [by_name, by_code, by_description]:
            result_ids = {
                edge["node"]["id"]
                for edge in response.data["documentTypes"]["edges"]
            }
            self.assertIn(self.to_global_id(self.document_type), result_ids)

    def test_document_types_are_multi_tenant_scoped(self):
        other_company = baker.make(MultiTenantCompany)
        hidden_document_type = DocumentType.objects.create(
            name="Hidden External Certificate",
            description="Only for another tenant",
            multi_tenant_company=other_company,
        )

        query = """
            query ($search: String!) {
              documentTypes(filters: {search: $search}) {
                edges {
                  node {
                    id
                  }
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"search": "Hidden External Certificate"},
        )

        self.assertIsNone(resp.errors)
        returned_ids = {
            edge["node"]["id"]
            for edge in resp.data["documentTypes"]["edges"]
        }
        self.assertNotIn(self.to_global_id(hidden_document_type), returned_ids)
