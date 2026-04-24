from core.schema.core.mutations import create, delete, type, update, List

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
