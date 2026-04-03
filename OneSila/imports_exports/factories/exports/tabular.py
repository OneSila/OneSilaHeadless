import copy
import csv
import json
from collections import OrderedDict
from io import BytesIO, StringIO

from openpyxl import Workbook

from core.helpers import ensure_serializable


KNOWN_COLLECTION_PREFIXES = {
    "images": "image",
    "documents": "document",
    "videos": "video",
    "prices": "price",
    "sales_pricelist_items": "sales_pricelist_item",
    "sales_channels": "sales_channel",
    "property_select_values": "property_select_value",
    "items": "item",
}

KNOWN_FIELD_ALIASES = {
    "images": {
        "image_url": "url",
    },
    "documents": {
        "document_url": "url",
    },
    "videos": {
        "video_url": "url",
    },
}

PRODUCT_VARIATION_PREFIXES = {
    "variations": {
        "configurable_parent_sku": "configurable_parent_sku",
        "configurable_product_sku": "configurable_product_sku",
    },
    "bundle_variations": {
        "bundle_parent_sku": "bundle_parent_sku",
        "bundle_product_sku": "bundle_product_sku",
    },
    "alias_variations": {
        "alias_parent_sku": "alias_parent_sku",
    },
}


def _join_values(*, values):
    cleaned = []
    for value in values:
        if value in (None, ""):
            continue
        normalized = str(value)
        if normalized not in cleaned:
            cleaned.append(normalized)
    return "|".join(cleaned)


def _normalize_header_key(*, value):
    if value is None:
        return "field"
    normalized = str(value).strip().lower()
    normalized = normalized.replace(" ", "_").replace("-", "_").replace(".", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized or "field"


def _stringify_complex(*, value):
    return json.dumps(
        ensure_serializable(value),
        ensure_ascii=False,
        sort_keys=True,
    )


def _serialize_cell_value(*, value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return _join_values(values=[_serialize_cell_value(value=item) for item in value])
    if isinstance(value, dict):
        return _stringify_complex(value=value)
    return str(value)


class TabularExportBuilder:
    def __init__(self, *, export_process, raw_data=None):
        self.export_process = export_process
        self.kind = export_process.kind
        source_data = export_process.raw_data if raw_data is None else raw_data
        self.raw_data = ensure_serializable(source_data)

    def build(self):
        headers = []
        seen_headers = set()
        row_maps = []

        for record in self._normalize_records():
            for expanded_record in self._expand_record(record=record):
                row = OrderedDict()
                self._flatten_mapping(
                    prefix="",
                    mapping=expanded_record,
                    row=row,
                )
                row_maps.append(row)
                for header in row.keys():
                    if header in seen_headers:
                        continue
                    seen_headers.add(header)
                    headers.append(header)

        return headers, row_maps

    def to_csv_bytes(self):
        headers, row_maps = self.build()
        stream = StringIO()
        writer = csv.writer(stream)
        writer.writerow(headers)
        for row in row_maps:
            writer.writerow(
                [_serialize_cell_value(value=row.get(header)) for header in headers]
            )
        return stream.getvalue().encode("utf-8-sig")

    def to_excel_bytes(self):
        headers, row_maps = self.build()
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = self.kind[:31] or "export"
        worksheet.append(headers)
        for row in row_maps:
            worksheet.append(
                [_serialize_cell_value(value=row.get(header)) for header in headers]
            )

        output = BytesIO()
        workbook.save(output)
        return output.getvalue()

    def _normalize_records(self):
        if isinstance(self.raw_data, list):
            return self.raw_data
        if isinstance(self.raw_data, dict):
            return [self.raw_data]
        return []

    def _expand_record(self, *, record):
        if self.kind != "products" or not isinstance(record, dict):
            return [record]

        base_record = copy.deepcopy(record)
        expanded_rows = []

        variation_collections = {
            key: base_record.pop(key, [])
            for key in PRODUCT_VARIATION_PREFIXES.keys()
        }
        expanded_rows.append(base_record)

        parent_sku = record.get("sku")
        for collection_key, extra_fields in PRODUCT_VARIATION_PREFIXES.items():
            for item in variation_collections.get(collection_key) or []:
                if not isinstance(item, dict):
                    continue
                variation_data = copy.deepcopy(item.get("variation_data") or {})
                if not variation_data:
                    continue

                for field_name, field_value in extra_fields.items():
                    variation_data[field_name] = parent_sku

                if collection_key == "bundle_variations" and "quantity" in item:
                    variation_data["quantity"] = item.get("quantity")

                expanded_rows.append(variation_data)

        return expanded_rows

    def _compose_key(self, *, prefix, key):
        key = _normalize_header_key(value=key)
        if prefix:
            return f"{prefix}_{key}"
        return key

    def _merge_value(self, *, row, key, value):
        value = _serialize_cell_value(value=value)
        current_value = row.get(key)
        if current_value in (None, ""):
            row[key] = value
            return
        if current_value == value:
            return
        row[key] = _join_values(values=[current_value, value])

    def _flatten_mapping(self, *, prefix, mapping, row, field_aliases=None):
        for key, value in mapping.items():
            alias_key = field_aliases.get(key, key) if field_aliases else key
            self._flatten_value(
                prefix=prefix,
                key=alias_key,
                value=value,
                row=row,
            )

    def _flatten_value(self, *, prefix, key, value, row):
        header_key = self._compose_key(prefix=prefix, key=key)

        if value is None:
            return

        if isinstance(value, dict):
            self._flatten_mapping(prefix=header_key, mapping=value, row=row)
            return

        if isinstance(value, list):
            if key == "translations":
                self._flatten_translations(prefix=prefix, translations=value, row=row)
                return
            if key == "properties":
                self._flatten_properties(properties=value, row=row)
                return
            if key == "configurator_select_values":
                self._flatten_configurator_values(values=value, row=row)
                return
            self._flatten_list(
                prefix=prefix,
                key=key,
                items=value,
                row=row,
            )
            return

        row[header_key] = value

    def _flatten_translations(self, *, prefix, translations, row):
        for translation in translations:
            if not isinstance(translation, dict):
                continue

            language = translation.get("language") or "default"
            sales_channel = translation.get("sales_channel")
            sales_channel_token = "default" if sales_channel is None else str(sales_channel)

            for field_name, field_value in translation.items():
                if field_name in {"language", "sales_channel"}:
                    continue

                if isinstance(field_value, list):
                    field_value = _join_values(values=field_value)
                elif isinstance(field_value, dict):
                    field_value = _stringify_complex(value=field_value)

                header = _normalize_header_key(
                    value=f"{prefix}_{field_name}_{language}_sc_{sales_channel_token}"
                    if prefix
                    else f"translation_{field_name}_{language}_sc_{sales_channel_token}"
                )
                row[header] = field_value

    def _flatten_properties(self, *, properties, row):
        for property_item in properties:
            if not isinstance(property_item, dict):
                continue

            property_data = property_item.get("property") or property_item.get("property_data") or {}
            internal_name = property_data.get("internal_name") or property_data.get("name") or "property"
            header_key = _normalize_header_key(value=internal_name)

            value = property_item.get("value")
            values = property_item.get("values")
            requirement = property_item.get("requirement")

            if value is None and values is not None:
                value = self._property_values_to_scalar(values=values)

            if value is not None:
                self._merge_value(row=row, key=header_key, value=value)

            if values not in (None, [], [{"value": value}] if value is not None else []):
                row[f"{header_key}_values"] = self._property_values_to_scalar(values=values)

            if requirement is not None:
                row[f"{header_key}_requirement"] = requirement

    def _property_values_to_scalar(self, *, values):
        if values is None:
            return None
        if isinstance(values, list):
            flattened = []
            for item in values:
                if isinstance(item, dict):
                    if "value" in item:
                        flattened.append(_serialize_cell_value(value=item["value"]))
                    else:
                        flattened.append(_stringify_complex(value=item))
                else:
                    flattened.append(_serialize_cell_value(value=item))
            return _join_values(values=flattened)
        return _serialize_cell_value(value=values)

    def _flatten_configurator_values(self, *, values, row):
        for item in values:
            if not isinstance(item, dict):
                continue
            property_data = item.get("property") or item.get("property_data") or {}
            internal_name = property_data.get("internal_name") or property_data.get("name") or "configurator"
            header_key = _normalize_header_key(value=f"configurator_{internal_name}")
            self._merge_value(row=row, key=header_key, value=item.get("value"))

    def _flatten_list(self, *, prefix, key, items, row):
        if not items:
            return

        if all(not isinstance(item, (dict, list)) for item in items):
            row[self._compose_key(prefix=prefix, key=key)] = _join_values(values=items)
            return

        item_prefix_base = KNOWN_COLLECTION_PREFIXES.get(key, key[:-1] if key.endswith("s") else key)
        field_aliases = KNOWN_FIELD_ALIASES.get(key, {})

        for index, item in enumerate(items, start=1):
            item_prefix = self._compose_key(
                prefix=prefix,
                key=f"{item_prefix_base}_{index}",
            )

            if isinstance(item, dict):
                self._flatten_mapping(
                    prefix=item_prefix,
                    mapping=item,
                    row=row,
                    field_aliases=field_aliases,
                )
                continue

            if isinstance(item, list):
                row[item_prefix] = _join_values(values=item)
                continue

            row[item_prefix] = item


def build_tabular_export(*, export_process, raw_data=None):
    return TabularExportBuilder(export_process=export_process, raw_data=raw_data).build()


def build_csv_export_content(*, export_process, raw_data=None):
    return TabularExportBuilder(export_process=export_process, raw_data=raw_data).to_csv_bytes()


def build_excel_export_content(*, export_process, raw_data=None):
    return TabularExportBuilder(export_process=export_process, raw_data=raw_data).to_excel_bytes()
