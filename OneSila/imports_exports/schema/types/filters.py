from typing import Optional

from django.db.models import Q
import strawberry
from strawberry import UNSET
from strawberry.relay import GlobalID

from core.schema.core.types.filters import SearchFilterMixin, filter
from core.schema.core.types.types import auto
from strawberry_django import filter_field as custom_filter
from imports_exports.models import Export, Import, ImportBrokenRecord, MappedImport


@filter(Import)
class ImportFilter(SearchFilterMixin):
    id: auto
    name: auto
    status: auto
    created_at: auto


@filter(MappedImport)
class MappedImportFilter(SearchFilterMixin):
    id: auto
    name: auto
    status: auto
    type: auto
    language: auto
    is_periodic: auto
    skip_broken_records: auto
    created_at: auto


@filter(Export)
class ExportFilter(SearchFilterMixin):
    id: auto
    name: auto
    status: auto
    type: auto
    kind: auto
    language: auto
    is_periodic: auto
    created_at: auto


@strawberry.input
class GlobalIdLookupInput:
    id: GlobalID | None = None


@filter(ImportBrokenRecord)
class ImportBrokenRecordFilter(SearchFilterMixin):
    id: auto
    import_process: Optional[ImportFilter]
    created_at: auto

    @custom_filter(name="mappedImport")
    def mapped_import(
        self,
        queryset,
        value: Optional[GlobalIdLookupInput],
        prefix: str,
    ):
        if value in (None, UNSET):
            return queryset, Q()

        mapped_import_id = getattr(value, "id", UNSET)
        if mapped_import_id in (None, UNSET):
            return queryset, Q()

        return queryset, Q(import_process_id=int(mapped_import_id.node_id))
