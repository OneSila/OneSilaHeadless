from core.schema.core.subscriptions import AsyncGenerator, Info, model_subscriber, subscription, type
from imports_exports.models import Export, MappedImport

from .types.types import ExportType, MappedImportType


@type(name="Subscription")
class ImportsExportsSubscription:
    @subscription
    async def mapped_import(self, info: Info, pk: str) -> AsyncGenerator[MappedImportType, None]:
        async for instance in model_subscriber(info=info, pk=pk, model=MappedImport):
            yield instance

    @subscription
    async def export(self, info: Info, pk: str) -> AsyncGenerator[ExportType, None]:
        async for instance in model_subscriber(info=info, pk=pk, model=Export):
            yield instance
