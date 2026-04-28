from core.schema.core.types.input import input, NodeInput, partial

from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState


@input(Workflow, fields="__all__")
class WorkflowInput:
    pass


@partial(Workflow, fields="__all__")
class WorkflowPartialInput(NodeInput):
    pass


@input(WorkflowState, fields="__all__")
class WorkflowStateInput:
    pass


@partial(WorkflowState, fields="__all__")
class WorkflowStatePartialInput(NodeInput):
    pass


@input(WorkflowProductAssignment, fields="__all__")
class WorkflowProductAssignmentInput:
    pass


@partial(WorkflowProductAssignment, fields="__all__")
class WorkflowProductAssignmentPartialInput(NodeInput):
    pass
