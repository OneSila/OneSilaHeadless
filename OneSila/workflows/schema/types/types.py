from typing import Annotated, List, Optional

from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.core.types.types import field, lazy, relay, type

from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState
from workflows.schema.types.filters import (
    WorkflowFilter,
    WorkflowProductAssignmentFilter,
    WorkflowStateFilter,
)
from workflows.schema.types.ordering import (
    WorkflowOrder,
    WorkflowProductAssignmentOrder,
    WorkflowStateOrder,
)


@type(Workflow, filters=WorkflowFilter, order=WorkflowOrder, pagination=True, fields="__all__")
class WorkflowType(relay.Node, GetQuerysetMultiTenantMixin):
    states: List[Annotated["WorkflowStateType", lazy("workflows.schema.types.types")]]
    product_assignments: List[Annotated["WorkflowProductAssignmentType", lazy("workflows.schema.types.types")]]

    @field()
    def products_count(self, info) -> int:
        return self.product_assignments.count()


@type(WorkflowState, filters=WorkflowStateFilter, order=WorkflowStateOrder, pagination=True, fields="__all__")
class WorkflowStateType(relay.Node, GetQuerysetMultiTenantMixin):
    workflow: Optional[Annotated["WorkflowType", lazy("workflows.schema.types.types")]]
    assignments: List[Annotated["WorkflowProductAssignmentType", lazy("workflows.schema.types.types")]]

    @field()
    def full_name(self, info) -> str:
        return f"{self.workflow.name} > {self.value}"


@type(
    WorkflowProductAssignment,
    filters=WorkflowProductAssignmentFilter,
    order=WorkflowProductAssignmentOrder,
    pagination=True,
    fields="__all__",
)
class WorkflowProductAssignmentType(relay.Node, GetQuerysetMultiTenantMixin):
    workflow: Optional[Annotated["WorkflowType", lazy("workflows.schema.types.types")]]
    workflow_state: Optional[Annotated["WorkflowStateType", lazy("workflows.schema.types.types")]]
    product: Optional[Annotated["ProductType", lazy("products.schema.types.types")]]
