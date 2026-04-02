from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from imports_exports.models import Export, Import, ImportBrokenRecord, MappedImport


@order(Import)
class ImportOrder:
    id: auto
    name: auto
    status: auto
    created_at: auto
    updated_at: auto
    percentage: auto


@order(MappedImport)
class MappedImportOrder:
    id: auto
    name: auto
    status: auto
    type: auto
    language: auto
    created_at: auto
    updated_at: auto
    percentage: auto


@order(Export)
class ExportOrder:
    id: auto
    name: auto
    status: auto
    type: auto
    kind: auto
    language: auto
    created_at: auto
    updated_at: auto
    percentage: auto


@order(ImportBrokenRecord)
class ImportBrokenRecordOrder:
    id: auto
    created_at: auto
    updated_at: auto
