from core.schema.core.queries import DjangoListConnection, connection, node, type

from .types.types import ExportType, ImportBrokenRecordType, ImportType, MappedImportType


@type(name="Query")
class ImportsExportsQuery:
    mapped_import: MappedImportType = node()
    mapped_imports: DjangoListConnection[MappedImportType] = connection()
    export: ExportType = node()
    exports: DjangoListConnection[ExportType] = connection()
    import_broken_record: ImportBrokenRecordType = node()
    import_broken_records: DjangoListConnection[ImportBrokenRecordType] = connection()
