from django.test import TransactionTestCase
from model_bakery import baker

from core.models import MultiTenantCompany
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import Product
from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


class WorkflowQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            description="Workflow for adding products",
            sort_order=10,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.assignment = WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=self.product,
            workflow_state=self.workflow_state,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_workflow_node_query(self):
        query = """
            query ($id: GlobalID!) {
              workflow(id: $id) {
                id
                name
                code
                description
                sortOrder
                autoAddOnProduct
                productsCount
                states {
                  id
                  value
                  code
                  sortOrder
                  isDefault
                  fullName
                }
                productAssignments {
                  id
                  workflowState {
                    id
                    code
                  }
                  product {
                    id
                  }
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"id": self.to_global_id(self.workflow)},
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["workflow"]
        self.assertEqual(payload["id"], self.to_global_id(self.workflow))
        self.assertEqual(payload["name"], "Add Products")
        self.assertEqual(payload["code"], "ADD_PRODUCTS")
        self.assertEqual(payload["description"], "Workflow for adding products")
        self.assertEqual(payload["sortOrder"], 10)
        self.assertFalse(payload["autoAddOnProduct"])
        self.assertEqual(payload["productsCount"], 1)
        self.assertEqual(len(payload["states"]), 1)
        self.assertEqual(payload["states"][0]["value"], "Untouched")
        self.assertEqual(payload["states"][0]["sortOrder"], 10)
        self.assertTrue(payload["states"][0]["isDefault"])
        self.assertEqual(payload["states"][0]["fullName"], "Add Products > Untouched")
        self.assertEqual(len(payload["productAssignments"]), 1)
        self.assertEqual(payload["productAssignments"][0]["workflowState"]["code"], "UNTOUCHED")
        self.assertEqual(self.from_global_id(payload["productAssignments"][0]["product"]["id"])[1], str(self.product.id))

    def test_workflows_search_is_multi_tenant_scoped(self):
        other_company = baker.make(MultiTenantCompany)
        hidden_workflow = Workflow.objects.create(
            name="Hidden Workflow",
            code="HIDDEN_WORKFLOW",
            multi_tenant_company=other_company,
        )

        query = """
            query ($search: String!) {
              workflows(filters: {search: $search}) {
                edges {
                  node {
                    id
                    code
                  }
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"search": "WORKFLOW"},
        )

        self.assertIsNone(resp.errors)
        returned_ids = {
            edge["node"]["id"]
            for edge in resp.data["workflows"]["edges"]
        }
        self.assertIn(self.to_global_id(self.workflow), returned_ids)
        self.assertNotIn(self.to_global_id(hidden_workflow), returned_ids)

    def test_product_node_exposes_workflowproductassignment_set(self):
        query = """
            query ($id: GlobalID!) {
              product(id: $id) {
                id
                workflowproductassignmentSet {
                  id
                  workflow {
                    id
                    code
                  }
                  workflowState {
                    id
                    code
                  }
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=query,
            variables={"id": self.to_global_id(self.product)},
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["product"]
        self.assertEqual(payload["id"], self.to_global_id(self.product))
        self.assertEqual(len(payload["workflowproductassignmentSet"]), 1)
        self.assertEqual(
            payload["workflowproductassignmentSet"][0]["workflow"]["code"],
            "ADD_PRODUCTS",
        )
        self.assertEqual(
            payload["workflowproductassignmentSet"][0]["workflowState"]["code"],
            "UNTOUCHED",
        )
