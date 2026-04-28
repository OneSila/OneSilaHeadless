from typing import Optional

from core.schema.core.types.filters import filter, SearchFilterMixin
from core.schema.core.types.types import auto
from products.schema.types.filters import ProductFilter

from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


@filter(Workflow)
class WorkflowFilter(SearchFilterMixin):
    id: auto
    name: auto
    code: auto
    sort_order: auto


@filter(WorkflowState)
class WorkflowStateFilter(SearchFilterMixin):
    id: auto
    workflow: Optional[WorkflowFilter]
    value: auto
    code: auto
    sort_order: auto
    is_default: auto


@filter(WorkflowProductAssignment)
class WorkflowProductAssignmentFilter(SearchFilterMixin):
    id: auto
    workflow: Optional[WorkflowFilter]
    workflow_state: Optional[WorkflowStateFilter]
    product: Optional[ProductFilter]
