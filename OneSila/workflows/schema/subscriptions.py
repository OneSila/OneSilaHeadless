from core.schema.core.subscriptions import AsyncGenerator, Info, model_subscriber, subscription, type

from workflows.models import Workflow, WorkflowProductAssignment, WorkflowState
from workflows.schema.types.types import WorkflowProductAssignmentType, WorkflowStateType, WorkflowType


@type(name="Subscription")
class WorkflowsSubscription:
    @subscription
    async def workflow(self, info: Info, pk: str) -> AsyncGenerator[WorkflowType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Workflow):
            yield i

    @subscription
    async def workflow_state(self, info: Info, pk: str) -> AsyncGenerator[WorkflowStateType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=WorkflowState):
            yield i

    @subscription
    async def workflow_product_assignment(
        self,
        info: Info,
        pk: str,
    ) -> AsyncGenerator[WorkflowProductAssignmentType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=WorkflowProductAssignment):
            yield i
