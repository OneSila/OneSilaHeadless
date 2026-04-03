from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from strawberry import UNSET
from strawberry.relay import GlobalID
from strawberry.types import Info
from strawberry_django.auth.utils import get_current_user

from core.schema.core.helpers import get_multi_tenant_company
from eancodes.models import EanCode
from imports_exports.factories.exports.registry import get_export_factory
from imports_exports.models import Export, Import, MappedImport
from media.models import Media
from products.models import Product
from properties.models import Property, PropertySelectValue, ProductPropertiesRule
from sales_channels.models import SalesChannel
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem


EXPORT_ID_MODELS = {
    Export.KIND_PRODUCTS: Product,
    Export.KIND_PROPERTIES: Property,
    Export.KIND_PROPERTY_SELECT_VALUES: PropertySelectValue,
    Export.KIND_IMAGES: Media,
    Export.KIND_DOCUMENTS: Media,
    Export.KIND_VIDEOS: Media,
    Export.KIND_SALES_PRICES: SalesPrice,
    Export.KIND_PRICE_LISTS: SalesPriceList,
    Export.KIND_PRICE_LIST_PRICES: SalesPriceListItem,
    Export.KIND_RULES: ProductPropertiesRule,
    Export.KIND_EAN_CODES: EanCode,
}

EXPORT_ALLOWED_PARAMETERS = {
    Export.KIND_PRODUCTS: {
        "sales_channel",
        "active_only",
        "flat",
        "add_translations",
        "values_are_ids",
        "add_value_ids",
        "product_properties_add_value_ids",
    },
    Export.KIND_PROPERTIES: {
        "property_select_values_add_value_ids",
    },
    Export.KIND_PROPERTY_SELECT_VALUES: {
        "add_value_ids",
        "values_are_ids",
    },
    Export.KIND_IMAGES: {
        "sales_channel",
        "add_product_sku",
        "add_title",
        "add_description",
    },
    Export.KIND_DOCUMENTS: {
        "sales_channel",
        "add_product_sku",
        "add_title",
        "add_description",
    },
    Export.KIND_VIDEOS: {
        "sales_channel",
        "add_product_sku",
        "add_title",
        "add_description",
    },
    Export.KIND_SALES_PRICES: {
        "add_product_sku",
    },
    Export.KIND_PRICE_LISTS: set(),
    Export.KIND_PRICE_LIST_PRICES: {
        "salespricelist",
        "add_product_sku",
    },
    Export.KIND_RULES: {
        "sales_channel",
    },
    Export.KIND_EAN_CODES: {
        "add_product_sku",
    },
}


def _get_company_and_user(*, info: Info):
    return (
        get_multi_tenant_company(info, fail_silently=False),
        get_current_user(info),
    )


def _resolve_node_ids(*, global_ids, model, multi_tenant_company, field_name: str) -> list[int]:
    if not global_ids:
        return []

    ids = [int(global_id.node_id) for global_id in global_ids]
    unique_ids = list(dict.fromkeys(ids))
    found_ids = set(
        model.objects.filter(
            multi_tenant_company=multi_tenant_company,
            id__in=unique_ids,
        ).values_list("id", flat=True)
    )
    missing_ids = [instance_id for instance_id in unique_ids if instance_id not in found_ids]
    if missing_ids:
        raise ValidationError({field_name: "One or more IDs are invalid for this company."})
    return unique_ids


def _resolve_optional_fk_id(
    *,
    global_id: GlobalID | None,
    model,
    multi_tenant_company,
    field_name: str,
) -> int | None:
    if global_id in (None, UNSET):
        return None
    return _resolve_node_ids(
        global_ids=[global_id],
        model=model,
        multi_tenant_company=multi_tenant_company,
        field_name=field_name,
    )[0]


def _validate_mapped_import_source(*, json_file, json_url):
    if json_file and json_url:
        raise ValidationError("Provide either json_file or json_url, not both.")


def create_mapped_import_instance(*, info: Info, data) -> MappedImport:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    _validate_mapped_import_source(json_file=data.json_file, json_url=data.json_url)

    instance = MappedImport(
        multi_tenant_company=multi_tenant_company,
        created_by_multi_tenant_user=current_user,
        last_update_by_multi_tenant_user=current_user,
        status=Import.STATUS_PENDING,
        name=data.name,
        create_only=data.create_only,
        update_only=data.update_only,
        override_only=data.override_only,
        skip_broken_records=data.skip_broken_records,
        type=data.type,
        is_periodic=data.is_periodic,
        interval_hours=data.interval_hours,
        language=data.language,
        json_file=data.json_file,
        json_url=data.json_url,
    )
    instance.full_clean()
    instance.save()
    return instance


def update_mapped_import_instance(*, info: Info, data) -> MappedImport:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    instance = MappedImport.objects.filter(
        id=data.id.node_id,
        multi_tenant_company=multi_tenant_company,
    ).first()
    if instance is None:
        raise PermissionDenied("Invalid company")

    updates = {
        "name": data.name,
        "create_only": data.create_only,
        "update_only": data.update_only,
        "override_only": data.override_only,
        "skip_broken_records": data.skip_broken_records,
        "is_periodic": data.is_periodic,
        "interval_hours": data.interval_hours,
        "language": data.language,
        "json_file": data.json_file,
        "json_url": data.json_url,
    }
    json_file_value = updates["json_file"]
    json_url_value = updates["json_url"]
    effective_json_file = instance.json_file if json_file_value is UNSET else json_file_value
    effective_json_url = instance.json_url if json_url_value is UNSET else json_url_value
    _validate_mapped_import_source(json_file=effective_json_file, json_url=effective_json_url)

    for field_name, value in updates.items():
        if value is not UNSET:
            setattr(instance, field_name, value)

    instance.last_update_by_multi_tenant_user = current_user
    instance.full_clean()
    instance.save()
    return instance


def resync_mapped_import_instance(*, info: Info, global_id: GlobalID) -> MappedImport:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    instance = MappedImport.objects.filter(
        id=global_id.node_id,
        multi_tenant_company=multi_tenant_company,
    ).first()
    if instance is None:
        raise PermissionDenied("Invalid company")

    instance.status = Import.STATUS_PENDING
    instance.percentage = 0
    instance.processed_records = 0
    instance.error_traceback = ""
    instance.last_update_by_multi_tenant_user = current_user
    instance.save(
        update_fields=[
            "status",
            "percentage",
            "processed_records",
            "error_traceback",
            "last_update_by_multi_tenant_user",
        ]
    )
    return instance


def _collect_input_values(*, data, names: list[str], include_none: bool) -> dict[str, Any]:
    values = {}
    for name in names:
        value = getattr(data, name, UNSET)
        if value is UNSET:
            continue
        if value is None and not include_none:
            continue
        if isinstance(value, list) and not value and not include_none:
            continue
        values[name] = value
    return values


def _merge_parameter_dicts(*, existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing or {})
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_parameter_dicts(
                existing=merged[key],
                updates=value,
            )
            continue
        merged[key] = value
    return merged


def _build_export_parameters(
    *,
    data,
    kind: str,
    multi_tenant_company,
    allow_ids: bool,
    include_none: bool,
) -> dict[str, Any]:
    allowed = EXPORT_ALLOWED_PARAMETERS[kind]
    provided = _collect_input_values(
        data=data,
        names=[
            "sales_channel",
            "salespricelist",
            "active_only",
            "flat",
            "add_translations",
            "values_are_ids",
            "add_value_ids",
            "add_product_sku",
            "add_title",
            "add_description",
            "product_properties_add_value_ids",
            "property_select_values_add_value_ids",
        ],
        include_none=include_none,
    )

    disallowed = sorted(set(provided.keys()) - allowed)
    if disallowed:
        raise ValidationError(
            {"parameters": f"Unsupported parameters for {kind}: {', '.join(disallowed)}"}
        )

    parameters = {}
    if allow_ids and getattr(data, "ids", None):
        id_model = EXPORT_ID_MODELS[kind]
        parameters["ids"] = _resolve_node_ids(
            global_ids=data.ids,
            model=id_model,
            multi_tenant_company=multi_tenant_company,
            field_name="ids",
        )

    if "sales_channel" in provided:
        parameters["sales_channel"] = _resolve_optional_fk_id(
            global_id=provided["sales_channel"],
            model=SalesChannel,
            multi_tenant_company=multi_tenant_company,
            field_name="sales_channel",
        )

    if "salespricelist" in provided:
        parameters["salespricelist"] = _resolve_node_ids(
            global_ids=provided["salespricelist"] or [],
            model=SalesPriceList,
            multi_tenant_company=multi_tenant_company,
            field_name="salespricelist",
        )

    for direct_key in (
        "active_only",
        "flat",
        "add_translations",
        "values_are_ids",
        "add_value_ids",
        "add_product_sku",
        "add_title",
        "add_description",
    ):
        if direct_key in provided:
            parameters[direct_key] = provided[direct_key]

    if "product_properties_add_value_ids" in provided:
        parameters.setdefault("product_properties", {})["add_value_ids"] = provided[
            "product_properties_add_value_ids"
        ]

    if "property_select_values_add_value_ids" in provided:
        parameters.setdefault("property_select_values", {})["add_value_ids"] = provided[
            "property_select_values_add_value_ids"
        ]

    return parameters


def _validate_export_columns(*, kind: str, columns: list[str] | None):
    if not columns:
        return
    factory_class = get_export_factory(kind=kind)
    unsupported = sorted(set(columns) - set(factory_class.supported_columns))
    if unsupported:
        raise ValidationError(
            {"columns": f"Unsupported columns for {kind}: {', '.join(unsupported)}"}
        )


def _validate_periodic_export_size(*, instance: Export):
    factory_class = get_export_factory(kind=instance.kind)
    factory = factory_class(export_process=instance)
    try:
        factory.validate_periodic_record_limit()
    except ValueError as exc:
        raise ValidationError({"is_periodic": str(exc)}) from exc


def create_export_instance(*, info: Info, data) -> Export:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    _validate_export_columns(kind=data.kind, columns=data.columns)
    parameters = _build_export_parameters(
        data=data,
        kind=data.kind,
        multi_tenant_company=multi_tenant_company,
        allow_ids=True,
        include_none=False,
    )

    instance = Export(
        multi_tenant_company=multi_tenant_company,
        created_by_multi_tenant_user=current_user,
        last_update_by_multi_tenant_user=current_user,
        status=Export.STATUS_PENDING,
        name=data.name,
        type=data.type,
        kind=data.kind,
        parameters=parameters,
        columns=data.columns or [],
        language=data.language,
        is_periodic=data.is_periodic,
        interval_hours=data.interval_hours,
    )
    _validate_periodic_export_size(instance=instance)
    instance.full_clean()
    instance.save()
    return instance


def update_export_instance(*, info: Info, data) -> Export:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    instance = Export.objects.filter(
        id=data.id.node_id,
        multi_tenant_company=multi_tenant_company,
    ).first()
    if instance is None:
        raise PermissionDenied("Invalid company")

    type_value = instance.type if data.type is UNSET else data.type
    columns_value = instance.columns if data.columns is UNSET else (data.columns or [])
    _validate_export_columns(kind=instance.kind, columns=columns_value)

    parameter_payload = _build_export_parameters(
        data=data,
        kind=instance.kind,
        multi_tenant_company=multi_tenant_company,
        allow_ids=False,
        include_none=False,
    )
    if parameter_payload:
        instance.parameters = _merge_parameter_dicts(
            existing=instance.parameters or {},
            updates=parameter_payload,
        )

    updates = {
        "name": data.name,
        "type": data.type,
        "columns": data.columns,
        "language": data.language,
        "is_periodic": data.is_periodic,
        "interval_hours": data.interval_hours,
    }
    for field_name, value in updates.items():
        if value is UNSET:
            continue
        if field_name == "columns":
            setattr(instance, field_name, value or [])
        else:
            setattr(instance, field_name, value)

    instance.type = type_value
    instance.last_update_by_multi_tenant_user = current_user
    _validate_periodic_export_size(instance=instance)
    instance.full_clean()
    instance.save()
    return instance


def resync_export_instance(*, info: Info, global_id: GlobalID) -> Export:
    multi_tenant_company, current_user = _get_company_and_user(info=info)
    instance = Export.objects.filter(
        id=global_id.node_id,
        multi_tenant_company=multi_tenant_company,
    ).first()
    if instance is None:
        raise PermissionDenied("Invalid company")

    instance.status = Export.STATUS_PENDING
    instance.percentage = 0
    instance.error_traceback = ""
    instance.last_update_by_multi_tenant_user = current_user
    instance.save(
        update_fields=[
            "status",
            "percentage",
            "error_traceback",
            "last_update_by_multi_tenant_user",
        ]
    )
    return instance
