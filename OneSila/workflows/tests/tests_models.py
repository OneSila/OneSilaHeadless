from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from core.models import MultiTenantCompany
from products.models import Product
from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


class WorkflowModelTestCase(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="Tenant A")
        self.other_company = MultiTenantCompany.objects.create(name="Tenant B")
        self.workflow = Workflow.objects.create(
            name="Add Products",
            code="ADD_PRODUCTS",
            sort_order=10,
            multi_tenant_company=self.company,
        )

    def test_workflow_code_is_unique_per_company(self):
        with self.assertRaises(IntegrityError):
            Workflow.objects.create(
                name="Duplicate",
                code="ADD_PRODUCTS",
                multi_tenant_company=self.company,
            )

        other_workflow = Workflow.objects.create(
            name="Allowed in other tenant",
            code="ADD_PRODUCTS",
            multi_tenant_company=self.other_company,
        )
        self.assertIsNotNone(other_workflow.pk)

    def test_workflow_code_is_generated_from_name_when_empty(self):
        workflow = Workflow.objects.create(
            name="Add Products",
            multi_tenant_company=self.company,
        )

        self.assertEqual(workflow.code, "ADD_PRODUCTS")

    def test_only_one_default_state_per_workflow(self):
        WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )

        with self.assertRaises(IntegrityError):
            WorkflowState.objects.create(
                workflow=self.workflow,
                value="To Enrich Attributes",
                code="TO_ENRICH_ATTRIBUTES",
                sort_order=20,
                is_default=True,
                multi_tenant_company=self.company,
            )

    def test_workflow_state_code_is_generated_from_value_when_empty(self):
        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="To Enrich Attributes",
            sort_order=10,
            multi_tenant_company=self.company,
        )

        self.assertEqual(workflow_state.code, "TO_ENRICH_ATTRIBUTES")

    def test_product_assignment_is_unique_per_workflow_and_product(self):
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )

        WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=product,
            workflow_state=workflow_state,
            multi_tenant_company=self.company,
        )

        with self.assertRaises(IntegrityError):
            WorkflowProductAssignment.objects.create(
                workflow=self.workflow,
                product=product,
                workflow_state=workflow_state,
                multi_tenant_company=self.company,
            )

    def test_product_assignment_state_must_belong_to_same_workflow(self):
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )
        other_workflow = Workflow.objects.create(
            name="Other Workflow",
            code="OTHER_WORKFLOW",
            multi_tenant_company=self.company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=other_workflow,
            value="Other State",
            code="OTHER_STATE",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )

        with self.assertRaises(ValidationError):
            WorkflowProductAssignment.objects.create(
                workflow=self.workflow,
                product=product,
                workflow_state=workflow_state,
                multi_tenant_company=self.company,
            )

    def test_auto_add_on_product_creates_assignment_with_default_state(self):
        workflow = Workflow.objects.create(
            name="Auto Workflow",
            code="AUTO_WORKFLOW",
            auto_add_on_product=True,
            multi_tenant_company=self.company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )

        product = Product.objects.create(
            sku="auto-workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )

        assignment = WorkflowProductAssignment.objects.get(
            workflow=workflow,
            product=product,
        )
        self.assertEqual(assignment.workflow_state, workflow_state)

    def test_workflow_cannot_be_deleted_when_assignment_exists(self):
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )
        WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=product,
            workflow_state=workflow_state,
            multi_tenant_company=self.company,
        )

        with self.assertRaises(ProtectedError):
            self.workflow.delete()

    def test_workflow_state_cannot_be_deleted_when_assignment_exists(self):
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )
        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )
        WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=product,
            workflow_state=workflow_state,
            multi_tenant_company=self.company,
        )

        with self.assertRaises(ProtectedError):
            workflow_state.delete()

    def test_product_delete_cascades_assignment_delete(self):
        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            value="Untouched",
            code="UNTOUCHED",
            sort_order=10,
            is_default=True,
            multi_tenant_company=self.company,
        )
        product = Product.objects.create(
            sku="workflow-product",
            type=Product.SIMPLE,
            multi_tenant_company=self.company,
        )
        assignment = WorkflowProductAssignment.objects.create(
            workflow=self.workflow,
            product=product,
            workflow_state=workflow_state,
            multi_tenant_company=self.company,
        )

        product.delete()

        self.assertFalse(WorkflowProductAssignment.objects.filter(id=assignment.id).exists())
