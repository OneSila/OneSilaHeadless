from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from strawberry import Info
import strawberry_django

from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import create, delete, type, update, List
from products.models import Product
from products.schema.types.input import ProductPartialInput
from workflows.models import WorkflowProductAssignment, WorkflowState
from workflows.schema.types.input import (
    WorkflowInput,
    WorkflowPartialInput,
    WorkflowProductAssignmentInput,
    WorkflowProductAssignmentPartialInput,
    WorkflowStateInput,
    WorkflowStatePartialInput,
)
from workflows.schema.types.types import (
    WorkflowProductAssignmentType,
    WorkflowStateType,
    WorkflowType,
)


@type(name="Mutation")
class WorkflowsMutation:
    create_workflow: WorkflowType = create(WorkflowInput)
    create_workflows: List[WorkflowType] = create(List[WorkflowInput])
    update_workflow: WorkflowType = update(WorkflowPartialInput)
    delete_workflow: WorkflowType = delete()
    delete_workflows: List[WorkflowType] = delete(is_bulk=True)

    create_workflow_state: WorkflowStateType = create(WorkflowStateInput)
    create_workflow_states: List[WorkflowStateType] = create(List[WorkflowStateInput])
    update_workflow_state: WorkflowStateType = update(WorkflowStatePartialInput)
    delete_workflow_state: WorkflowStateType = delete()
    delete_workflow_states: List[WorkflowStateType] = delete(is_bulk=True)

    create_workflow_product_assignment: WorkflowProductAssignmentType = create(WorkflowProductAssignmentInput)
    create_workflow_product_assignments: List[WorkflowProductAssignmentType] = create(List[WorkflowProductAssignmentInput])
    update_workflow_product_assignment: WorkflowProductAssignmentType = update(WorkflowProductAssignmentPartialInput)
    delete_workflow_product_assignment: WorkflowProductAssignmentType = delete()
    delete_workflow_product_assignments: List[WorkflowProductAssignmentType] = delete(is_bulk=True)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def bulk_assign_workflow_state(
        self,
        *,
        workflow_state: WorkflowStatePartialInput,
        products: List[ProductPartialInput],
        info: Info,
    ) -> List[WorkflowProductAssignmentType]:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        if not getattr(workflow_state, "id", None):
            raise ValidationError(_("Workflow state is required."))

        try:
            state_obj = WorkflowState.objects.select_related("workflow").get(
                id=workflow_state.id.node_id,
                multi_tenant_company=multi_tenant_company,
            )
        except WorkflowState.DoesNotExist as exc:
            raise PermissionError("Invalid company") from exc

        product_ids = [int(product.id.node_id) for product in products if getattr(product, "id", None)]
        if not product_ids:
            raise ValidationError(_("No products were provided."))

        unique_product_ids = list(dict.fromkeys(product_ids))
        existing_product_ids = set(
            Product.objects.filter(
                id__in=unique_product_ids,
                multi_tenant_company=multi_tenant_company,
            ).values_list("id", flat=True)
        )
        if len(existing_product_ids) != len(unique_product_ids):
            raise PermissionError("Invalid company")

        with transaction.atomic():
            for product_id in unique_product_ids:
                assignment = WorkflowProductAssignment.objects.filter(
                    workflow_id=state_obj.workflow_id,
                    product_id=product_id,
                ).first()
                if assignment is None:
                    WorkflowProductAssignment.objects.create(
                        workflow_id=state_obj.workflow_id,
                        workflow_state_id=state_obj.id,
                        product_id=product_id,
                        multi_tenant_company=multi_tenant_company,
                    )
                    continue

                if assignment.workflow_state_id != state_obj.id:
                    assignment.workflow_state_id = state_obj.id
                    assignment.save(update_fields=["workflow_state"])

        updated_assignments = WorkflowProductAssignment.objects.filter(
            workflow_id=state_obj.workflow_id,
            product_id__in=unique_product_ids,
        ).select_related("workflow", "workflow_state", "product")
        updated_by_product_id = {assignment.product_id: assignment for assignment in updated_assignments}

        return [updated_by_product_id[product_id] for product_id in unique_product_ids]
