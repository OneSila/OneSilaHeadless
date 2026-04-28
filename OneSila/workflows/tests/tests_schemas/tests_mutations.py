from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from core.models import MultiTenantCompany
from model_bakery import baker
from products.models import Product
from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


class WorkflowMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_create_workflow(self):
        mutation = """
            mutation ($data: WorkflowInput!) {
              createWorkflow(data: $data) {
                id
                name
                code
                description
                sortOrder
                autoAddOnProduct
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "name": "Add Products",
                    "code": "ADD_PRODUCTS",
                    "description": "Workflow for adding products",
                    "sortOrder": 10,
                    "autoAddOnProduct": True,
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createWorkflow"]
        self.assertEqual(payload["name"], "Add Products")
        self.assertEqual(payload["code"], "ADD_PRODUCTS")
        self.assertEqual(payload["description"], "Workflow for adding products")
        self.assertEqual(payload["sortOrder"], 10)
        self.assertTrue(payload["autoAddOnProduct"])

    def test_create_workflow_generates_code_when_missing(self):
        mutation = """
            mutation ($data: WorkflowInput!) {
              createWorkflow(data: $data) {
                id
                name
                code
                description
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "name": "Add Products",
                    "description": "Workflow for adding products",
                    "sortOrder": 10,
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createWorkflow"]
        self.assertEqual(payload["name"], "Add Products")
        self.assertEqual(payload["code"], "ADD_PRODUCTS")
        self.assertEqual(payload["description"], "Workflow for adding products")

    def test_create_workflow_state(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: WorkflowStateInput!) {
              createWorkflowState(data: $data) {
                id
                value
                code
                sortOrder
                isDefault
                workflow {
                  id
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "workflow": {"id": self.to_global_id(workflow)},
                    "value": "Untouched",
                    "code": "UNTOUCHED",
                    "sortOrder": 10,
                    "isDefault": True,
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createWorkflowState"]
        self.assertEqual(payload["value"], "Untouched")
        self.assertEqual(payload["code"], "UNTOUCHED")
        self.assertEqual(payload["sortOrder"], 10)
        self.assertTrue(payload["isDefault"])
        self.assertEqual(payload["workflow"]["id"], self.to_global_id(workflow))

    def test_create_workflow_state_generates_code_when_missing(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: WorkflowStateInput!) {
              createWorkflowState(data: $data) {
                id
                value
                code
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "workflow": {"id": self.to_global_id(workflow)},
                    "value": "To Enrich Attributes",
                    "sortOrder": 10,
                    "isDefault": False,
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createWorkflowState"]
        self.assertEqual(payload["value"], "To Enrich Attributes")
        self.assertEqual(payload["code"], "TO_ENRICH_ATTRIBUTES")

    def test_create_workflow_product_assignment(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.multi_tenant_company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: WorkflowProductAssignmentInput!) {
              createWorkflowProductAssignment(data: $data) {
                id
                workflow {
                  id
                }
                workflowState {
                  id
                }
                product {
                  id
                }
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "workflow": {"id": self.to_global_id(workflow)},
                    "workflowState": {"id": self.to_global_id(workflow_state)},
                    "product": {"id": self.to_global_id(product)},
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createWorkflowProductAssignment"]
        self.assertEqual(payload["workflow"]["id"], self.to_global_id(workflow))
        self.assertEqual(payload["workflowState"]["id"], self.to_global_id(workflow_state))
        self.assertEqual(self.from_global_id(payload["product"]["id"])[1], str(product.id))
        self.assertTrue(
            WorkflowProductAssignment.objects.filter(
                workflow=workflow,
                product=product,
                workflow_state=workflow_state,
            ).exists()
        )

    def test_update_workflow(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            sort_order=10,
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: WorkflowPartialInput!) {
              updateWorkflow(data: $data) {
                id
                name
                sortOrder
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "id": self.to_global_id(workflow),
                    "name": "Enrich Products",
                    "sortOrder": 20,
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["updateWorkflow"]
        self.assertEqual(payload["name"], "Enrich Products")
        self.assertEqual(payload["sortOrder"], 20)
        workflow.refresh_from_db()
        self.assertEqual(workflow.name, "Enrich Products")
        self.assertEqual(workflow.sort_order, 20)

    def test_delete_workflow_state(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.multi_tenant_company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: NodeInput!) {
              deleteWorkflowState(data: $data) {
                id
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"data": {"id": self.to_global_id(workflow_state)}},
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(resp.data["deleteWorkflowState"]["id"], self.to_global_id(workflow_state))
        self.assertFalse(WorkflowState.objects.filter(id=workflow_state.id).exists())

    def test_bulk_assign_workflow_state_creates_assignments(self):
        workflow = Workflow.objects.create(
            name="Listing Flow",
            code="LISTING_FLOW",
            multi_tenant_company=self.multi_tenant_company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Ready",
            code="READY",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_1 = Product.objects.create(
            sku="workflow-bulk-product-1",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_2 = Product.objects.create(
            sku="workflow-bulk-product-2",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($workflowState: WorkflowStatePartialInput!, $products: [ProductPartialInput!]!) {
              bulkAssignWorkflowState(workflowState: $workflowState, products: $products) {
                id
                workflow {
                  id
                }
                workflowState {
                  id
                }
                product {
                  id
                }
              }
            }
        """

        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "workflowState": {"id": self.to_global_id(workflow_state)},
                "products": [{"id": self.to_global_id(product_1)}, {"id": self.to_global_id(product_2)}],
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["bulkAssignWorkflowState"]
        self.assertEqual(len(payload), 2)
        assignment_ids = {
            self.from_global_id(item["product"]["id"])[1] for item in payload
        }
        self.assertEqual(assignment_ids, {str(product_1.id), str(product_2.id)})
        self.assertTrue(
            WorkflowProductAssignment.objects.filter(
                workflow=workflow,
                workflow_state=workflow_state,
                product=product_1,
                multi_tenant_company=self.multi_tenant_company,
            ).exists()
        )
        self.assertTrue(
            WorkflowProductAssignment.objects.filter(
                workflow=workflow,
                workflow_state=workflow_state,
                product=product_2,
                multi_tenant_company=self.multi_tenant_company,
            ).exists()
        )

    def test_bulk_assign_workflow_state_updates_existing_assignment(self):
        workflow = Workflow.objects.create(
            name="Listing Flow",
            code="LISTING_FLOW",
            multi_tenant_company=self.multi_tenant_company,
        )
        old_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Old",
            code="OLD",
            multi_tenant_company=self.multi_tenant_company,
        )
        new_state = WorkflowState.objects.create(
            workflow=workflow,
            value="New",
            code="NEW",
            multi_tenant_company=self.multi_tenant_company,
        )
        product = Product.objects.create(
            sku="workflow-bulk-product-3",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        assignment = WorkflowProductAssignment.objects.create(
            workflow=workflow,
            workflow_state=old_state,
            product=product,
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($workflowState: WorkflowStatePartialInput!, $products: [ProductPartialInput!]!) {
              bulkAssignWorkflowState(workflowState: $workflowState, products: $products) {
                id
                workflowState {
                  id
                }
              }
            }
        """

        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "workflowState": {"id": self.to_global_id(new_state)},
                "products": [{"id": self.to_global_id(product)}],
            },
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(len(resp.data["bulkAssignWorkflowState"]), 1)
        assignment.refresh_from_db()
        self.assertEqual(assignment.workflow_state_id, new_state.id)

    def test_bulk_assign_workflow_state_rejects_other_company_products(self):
        workflow = Workflow.objects.create(
            name="Listing Flow",
            code="LISTING_FLOW",
            multi_tenant_company=self.multi_tenant_company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Ready",
            code="READY",
            multi_tenant_company=self.multi_tenant_company,
        )
        other_company = baker.make(MultiTenantCompany)
        other_product = Product.objects.create(
            sku="workflow-bulk-other-company-product",
            type=Product.SIMPLE,
            multi_tenant_company=other_company,
        )

        mutation = """
            mutation ($workflowState: WorkflowStatePartialInput!, $products: [ProductPartialInput!]!) {
              bulkAssignWorkflowState(workflowState: $workflowState, products: $products) {
                id
              }
            }
        """

        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "workflowState": {"id": self.to_global_id(workflow_state)},
                "products": [{"id": self.to_global_id(other_product)}],
            },
            asserts_errors=True,
        )

        self.assertIsNotNone(resp.errors)

    def test_bulk_assign_workflow_state_handles_existing_legacy_assignment(self):
        workflow = Workflow.objects.create(
            name="Listing Flow",
            code="LISTING_FLOW",
            multi_tenant_company=self.multi_tenant_company,
        )
        old_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Old",
            code="OLD",
            multi_tenant_company=self.multi_tenant_company,
        )
        new_state = WorkflowState.objects.create(
            workflow=workflow,
            value="New",
            code="NEW",
            multi_tenant_company=self.multi_tenant_company,
        )
        product = Product.objects.create(
            sku="workflow-bulk-product-legacy",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Simulate a legacy row missing tenant value.
        assignment = WorkflowProductAssignment.objects.create(
            workflow=workflow,
            workflow_state=old_state,
            product=product,
            multi_tenant_company=self.multi_tenant_company,
        )
        WorkflowProductAssignment.objects.filter(id=assignment.id).update(multi_tenant_company_id=None)

        mutation = """
            mutation ($workflowState: WorkflowStatePartialInput!, $products: [ProductPartialInput!]!) {
              bulkAssignWorkflowState(workflowState: $workflowState, products: $products) {
                id
                workflowState {
                  id
                }
              }
            }
        """

        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "workflowState": {"id": self.to_global_id(new_state)},
                "products": [{"id": self.to_global_id(product)}],
            },
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(len(resp.data["bulkAssignWorkflowState"]), 1)
        assignment.refresh_from_db()
        self.assertEqual(assignment.workflow_state_id, new_state.id)
