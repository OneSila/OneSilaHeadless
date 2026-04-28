from core.schema.core.queries import connection, DjangoListConnection, node, type

from workflows.schema.types.types import (
    WorkflowProductAssignmentType,
    WorkflowStateType,
    WorkflowType,
)


@type(name="Query")
class WorkflowsQuery:
    workflow: WorkflowType = node()
    workflows: DjangoListConnection[WorkflowType] = connection()

    workflow_state: WorkflowStateType = node()
    workflow_states: DjangoListConnection[WorkflowStateType] = connection()

    workflow_product_assignment: WorkflowProductAssignmentType = node()
    workflow_product_assignments: DjangoListConnection[WorkflowProductAssignmentType] = connection()
