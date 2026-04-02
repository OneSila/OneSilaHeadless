from core.schema.core.extensions import default_extensions
from core.schema.core.mutations import List, delete, type
from imports_exports.schema.types.input import (
    ExportCreateInput,
    ExportUpdateInput,
    MappedImportCreateInput,
    MappedImportUpdateInput,
)
from strawberry.relay import GlobalID
import strawberry_django

from .mutation_helpers import (
    create_export_instance,
    create_mapped_import_instance,
    resync_export_instance,
    resync_mapped_import_instance,
    update_export_instance,
    update_mapped_import_instance,
)
from .types.types import ExportType, MappedImportType


@type(name="Mutation")
class ImportsExportsMutation:
    delete_mapped_import: MappedImportType = delete()
    delete_mapped_imports: List[MappedImportType] = delete(is_bulk=True)
    delete_export: ExportType = delete()
    delete_exports: List[ExportType] = delete(is_bulk=True)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def create_mapped_import(self, info, *, data: MappedImportCreateInput) -> MappedImportType:
        return create_mapped_import_instance(info=info, data=data)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def update_mapped_import(self, info, *, data: MappedImportUpdateInput) -> MappedImportType:
        return update_mapped_import_instance(info=info, data=data)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def resync_mapped_import(self, info, *, id: GlobalID) -> MappedImportType:
        return resync_mapped_import_instance(info=info, global_id=id)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def create_export(self, info, *, data: ExportCreateInput) -> ExportType:
        return create_export_instance(info=info, data=data)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def update_export(self, info, *, data: ExportUpdateInput) -> ExportType:
        return update_export_instance(info=info, data=data)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def resync_export(self, info, *, id: GlobalID) -> ExportType:
        return resync_export_instance(info=info, global_id=id)
