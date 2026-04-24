from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


@order(Workflow)
class WorkflowOrder:
    id: auto
    name: auto
    code: auto
    sort_order: auto
    created_at: auto
    updated_at: auto


@order(WorkflowState)
class WorkflowStateOrder:
    id: auto
    workflow: auto
    value: auto
    code: auto
    sort_order: auto
    is_default: auto
    created_at: auto
    updated_at: auto


@order(WorkflowProductAssignment)
class WorkflowProductAssignmentOrder:
    id: auto
    workflow: auto
    workflow_state: auto
    product: auto
    created_at: auto
    updated_at: auto
