from typing import Annotated, List, Optional
from enum import Enum

import strawberry
from strawberry import lazy
from strawberry.relay import to_base64

from core.schema.core.types.types import GetQuerysetMultiTenantMixin, field, relay, type
from get_absolute_url.helpers import generate_absolute_url
from imports_exports.models import Export, Import, ImportBrokenRecord, MappedImport

from .filters import ExportFilter, ImportBrokenRecordFilter, MappedImportFilter
from .ordering import ExportOrder, ImportBrokenRecordOrder, MappedImportOrder


@strawberry.enum
class PercentageColorEnum(Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    GREEN = "GREEN"


def _resolve_percentage_color(*, status: str, percentage: int) -> PercentageColorEnum:
    if status == Import.STATUS_FAILED:
        return PercentageColorEnum.RED
    if status == Import.STATUS_SUCCESS and percentage == 100:
        return PercentageColorEnum.GREEN
    return PercentageColorEnum.ORANGE


def _build_file_url(*, file_field) -> str | None:
    if not file_field:
        return None
    return f"{generate_absolute_url(trailing_slash=False)}{file_field.url}"


@type(Import, fields="__all__")
class ImportType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def percentage_color(self) -> PercentageColorEnum:
        return _resolve_percentage_color(status=self.status, percentage=self.percentage)


@type(MappedImport, filters=MappedImportFilter, order=MappedImportOrder, pagination=True, fields="__all__")
class MappedImportType(relay.Node, GetQuerysetMultiTenantMixin):
    broken_record_entries: List[Annotated["ImportBrokenRecordType", lazy("imports_exports.schema.types.types")]]

    @field()
    def proxy_id(self, info) -> str:
        return to_base64(ImportType, self.pk)

    @field()
    def percentage_color(self) -> PercentageColorEnum:
        return _resolve_percentage_color(status=self.status, percentage=self.percentage)

    @field()
    def json_file_url(self) -> str | None:
        return _build_file_url(file_field=self.json_file)

    @field()
    def cleaned_errors(self) -> list[str]:
        return self.get_cleaned_errors_from_broken_records()


@type(Export, filters=ExportFilter, order=ExportOrder, pagination=True, fields="__all__")
class ExportType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def percentage_color(self) -> PercentageColorEnum:
        return _resolve_percentage_color(status=self.status, percentage=self.percentage)

    @field()
    def file_url(self) -> str | None:
        return _build_file_url(file_field=self.file)

    @field()
    def feed_url(self) -> str | None:
        if self.type != Export.TYPE_JSON_FEED or not self.feed_key:
            return None
        return f"{generate_absolute_url(trailing_slash=False)}/direct/export/{self.feed_key}/"


@type(
    ImportBrokenRecord,
    filters=ImportBrokenRecordFilter,
    order=ImportBrokenRecordOrder,
    pagination=True,
    fields="__all__",
)
class ImportBrokenRecordType(relay.Node, GetQuerysetMultiTenantMixin):
    import_process: Optional[Annotated["ImportType", lazy("imports_exports.schema.types.types")]]
