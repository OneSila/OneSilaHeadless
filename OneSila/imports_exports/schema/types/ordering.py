from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from imports_exports.models import Import

@order(Import)
class ImportOrder:
    id: auto