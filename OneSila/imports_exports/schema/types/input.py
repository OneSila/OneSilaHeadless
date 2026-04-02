from strawberry import UNSET
from strawberry.file_uploads import Upload
from strawberry.relay import GlobalID

from core.schema.core.types.input import strawberry_input


@strawberry_input
class MappedImportCreateInput:
    name: str | None = None
    create_only: bool = False
    update_only: bool = False
    override_only: bool = False
    skip_broken_records: bool = False
    type: str
    is_periodic: bool = False
    interval_hours: int | None = None
    language: str | None = None
    json_file: Upload | None = None
    json_url: str | None = None


@strawberry_input
class MappedImportUpdateInput:
    id: GlobalID
    name: str | None = UNSET
    create_only: bool | None = UNSET
    update_only: bool | None = UNSET
    override_only: bool | None = UNSET
    skip_broken_records: bool | None = UNSET
    is_periodic: bool | None = UNSET
    interval_hours: int | None = UNSET
    language: str | None = UNSET
    json_file: Upload | None = UNSET
    json_url: str | None = UNSET


@strawberry_input
class ExportCreateInput:
    name: str | None = None
    type: str
    kind: str
    columns: list[str] | None = None
    language: str | None = None
    is_periodic: bool = False
    interval_hours: int | None = None
    ids: list[GlobalID] | None = None
    sales_channel: GlobalID | None = None
    salespricelist: list[GlobalID] | None = None
    active_only: bool | None = None
    flat: bool | None = None
    add_translations: bool | None = None
    values_are_ids: bool | None = None
    add_value_ids: bool | None = None
    add_product_sku: bool | None = None
    add_title: bool | None = None
    add_description: bool | None = None
    product_properties_add_value_ids: bool | None = None
    property_select_values_add_value_ids: bool | None = None


@strawberry_input
class ExportUpdateInput:
    id: GlobalID
    name: str | None = UNSET
    type: str | None = UNSET
    columns: list[str] | None = UNSET
    language: str | None = UNSET
    is_periodic: bool | None = UNSET
    interval_hours: int | None = UNSET
    sales_channel: GlobalID | None = UNSET
    salespricelist: list[GlobalID] | None = UNSET
    active_only: bool | None = UNSET
    flat: bool | None = UNSET
    add_translations: bool | None = UNSET
    values_are_ids: bool | None = UNSET
    add_value_ids: bool | None = UNSET
    add_product_sku: bool | None = UNSET
    add_title: bool | None = UNSET
    add_description: bool | None = UNSET
    product_properties_add_value_ids: bool | None = UNSET
    property_select_values_add_value_ids: bool | None = UNSET
