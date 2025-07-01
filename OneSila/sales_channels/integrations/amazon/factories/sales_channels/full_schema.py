from spapi import DefinitionsApi

from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.decorators import throttle_safe
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, PullAmazonMixin
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannelView,
    AmazonDefaultUnitConfigurator,
)
from sales_channels.integrations.amazon.models.properties import AmazonProductType, AmazonPublicDefinition, \
    AmazonProperty, AmazonPropertySelectValue, AmazonProductTypeItem
import requests
import json
from properties.models import Property


class ExportDefinitionFactory:
    def __init__(self, public_definition: AmazonPublicDefinition):
        self.public_definition = public_definition
        self.results = []  # final flat list of export definitions
        self.current_path = [self.public_definition.code]  # tracks keys like battery > weight > value
        self.allow_not_mapped_keys = {"standardized_values", "other_than_listed"}

    def run(self):
        schema = self.public_definition.raw_schema
        self._walk(schema)
        return self.results

    def _walk(self, node):
        if not isinstance(node, dict):
            return

        # Dive into "items" first
        if "items" in node:
            self._walk(node["items"])
            return

        properties = node.get("properties", {})
        for key, value in properties.items():
            self.current_path.append(key)

            # Skip helper/meta keys
            if key in {"language_tag", "marketplace_id", "unit"}:
                self.current_path.pop()
                continue

            # Skip only other_than_listed for walk
            if key.endswith("other_than_listed"):
                self.current_path.pop()
                continue

            # If terminal value
            is_leaf = not isinstance(value, dict) or (
                        "type" in value and "items" not in value and "properties" not in value)

            if is_leaf:
                attr_code = self._compose_attr_code()
                parent_key = self.current_path[-2] if len(self.current_path) >= 2 else ""
                allow_not_mapped = any(k in parent_key for k in self.allow_not_mapped_keys)
                self._add_export(attr_code, value, allow_not_mapped)
                self.current_path.pop()
                continue

            # Recurse deeper
            self._walk(value)
            self.current_path.pop()

    def _compose_attr_code(self):
        # Filter out unwanted helper/meta keys from current_path
        keys = [
            k for k in self.current_path
            if k not in {"value", "unit", "language_tag", "marketplace_id"}
               and not any(ignore in k for ignore in self.allow_not_mapped_keys)
        ]
        return "__".join(keys)

    def map_amazon_type_to_property_type(self, value_schema: dict) -> str:
        """
        Converts Amazon schema type definition into internal Property.TYPES
        """
        value_type = value_schema.get("type")
        max_length = value_schema.get("maxLength")
        any_of = value_schema.get("anyOf", [])
        one_of = value_schema.get("oneOf", [])
        enums = value_schema.get("enum")

        if value_type == "array" and isinstance(value_schema.get("items"), dict):
            item_schema = value_schema["items"]
            max_items = value_schema.get("maxItems", 1)

            if "enum" in item_schema or self._any_of_has_enum(item_schema.get("anyOf", [])):
                return Property.TYPES.MULTISELECT if max_items > 1 else Property.TYPES.SELECT

            # Fallback to basic string or int check inside array
            item_type = item_schema.get("type")
            if item_type == "string":
                return Property.TYPES.MULTISELECT if max_items > 1 else Property.TYPES.TEXT
            elif item_type == "number":
                return Property.TYPES.FLOAT
            elif item_type == "integer":
                return Property.TYPES.INT

        # Handle boolean
        if value_type == "boolean":
            return Property.TYPES.BOOLEAN

        # Handle integer
        if value_type == "integer":
            return Property.TYPES.INT

        # Handle float
        if value_type == "number":
            return Property.TYPES.FLOAT

        # Handle enum/select/multiselect
        if enums or self._any_of_has_enum(any_of):
            # MultiSelect if parent array has maxItems > 1
            if value_schema.get("maxItems", 1) > 1:
                return Property.TYPES.MULTISELECT
            return Property.TYPES.SELECT

        # Handle DATE or DATETIME
        if one_of and value_type == "string":
            formats = [entry.get("format") for entry in one_of]
            if "date" in formats and "date-time" in formats:
                return Property.TYPES.DATE
            elif "date" in formats:
                return Property.TYPES.DATE
            elif "date-time" in formats:
                return Property.TYPES.DATETIME

        # Handle text vs description
        if value_type == "string":
            if max_length is not None and max_length > 1000:
                return Property.TYPES.DESCRIPTION
            return Property.TYPES.TEXT

        return Property.TYPES.TEXT  # default fallback

    def allows_not_mapped_values(self, value_schema: dict) -> bool:
        """
        Detect if this schema allows values outside of enum.
        True if:
        - anyOf has both enum and plain string (no enum)
        - OR schema contains a related *_other_than_listed field
        """
        any_of = value_schema.get("anyOf")
        has_anyof_fallback = any(
            isinstance(option, dict) and option.get("type") == "string" and "enum" not in option
            for option in any_of or []
        )

        # Step 1: Get the last meaningful key from the current path
        last_key = next(
            (k for k in reversed(self.current_path)
             if k not in {"value", "language_tag", "marketplace_id", "unit"}),
            None
        )
        if not last_key:
            return has_anyof_fallback

        # Step 2: Recursively check the raw schema for a *_other_than_listed that matches this key
        def has_matching_other_than_listed(node):
            if not isinstance(node, dict):
                return False

            # Always dive into `items` if it exists
            if "items" in node and isinstance(node["items"], dict):
                if has_matching_other_than_listed(node["items"]):
                    return True

            props = node.get("properties", {})
            for key, val in props.items():
                if key.endswith("_other_than_listed"):
                    base = key.replace("_other_than_listed", "")
                    if base == last_key:
                        return True

                # Recurse into deeper properties
                if isinstance(val, dict):
                    if has_matching_other_than_listed(val):
                        return True

            return False

        has_related_fallback_field = has_matching_other_than_listed(self.public_definition.raw_schema)

        return has_anyof_fallback or has_related_fallback_field

    def _any_of_has_enum(self, any_of_list: list) -> bool:
        return any("enum" in option for option in any_of_list if isinstance(option, dict))

    def extract_enum_values(self, value_schema: dict) -> list:
        """
        Extracts enum values from schema, including inside arrays and anyOf.
        Returns format: [{"value": ..., "name": ...}]
        """
        enums, enum_names = [], []

        # Handle array wrapper
        if value_schema.get("type") == "array" and isinstance(value_schema.get("items"), dict):
            value_schema = value_schema["items"]

        # Direct enum
        if "enum" in value_schema:
            enums = value_schema["enum"]
            enum_names = value_schema.get("enumNames", enums)
        else:
            # Look inside anyOf
            for option in value_schema.get("anyOf", []):
                if isinstance(option, dict) and "enum" in option:
                    enums = option["enum"]
                    enum_names = option.get("enumNames", enums)
                    break

        return [{"value": val, "name": name} for val, name in zip(enums, enum_names)]

    def _add_export(self, attr_code, value_schema, force_allow_not_mapped=False):

        # Always preserve the title from the original value_schema
        original_title = value_schema.get("title") or attr_code.replace("__", " ").title()

        # Check if there's a sibling standardized_values
        parent_schema = self._get_parent_schema()
        sibling_enum_schema = parent_schema.get("standardized_values") if isinstance(parent_schema, dict) else None
        if sibling_enum_schema:
            # override value_schema for enum-related logic
            value_schema = sibling_enum_schema
            force_allow_not_mapped = True

        export = {
            "code": attr_code,
            "name": original_title,
            "type": self.map_amazon_type_to_property_type(value_schema),
            "values": self.extract_enum_values(value_schema),
        }

        if force_allow_not_mapped or self.allows_not_mapped_values(value_schema):
            export["allow_not_mapped_values"] = True

        self.results.append(export)

    def _get_parent_schema(self):
        """
        Returns the parent-level `properties` schema based on the current path.
        Special handling when the path is at root level (just the attribute name).
        """
        schema = self.public_definition.raw_schema
        path = self.current_path[:-1]  # exclude current key (usually 'value' or similar)

        if len(path) == 1 and path[0] == self.public_definition.code:
            # Root-level attribute schema
            return schema.get("items", {}).get("properties", {})

        try:
            for key in path:
                schema = schema[key]
                if "items" in schema:
                    schema = schema["items"]
                if "properties" in schema:
                    schema = schema["properties"]
            return schema if isinstance(schema, dict) else {}
        except Exception:
            return {}


class UsageDefinitionFactory:
    def __init__(self, public_definition):
        self.public_definition = public_definition
        self.current_path = []

    def run(self):
        schema = self.public_definition.raw_schema or {}
        root_code = self.public_definition.code
        body = {root_code: self._process(schema.get(root_code, schema))}
        result = json.dumps(body, indent=2)
        return result

    def _process(self, node):
        if not isinstance(node, dict):
            return None

        if node.get("type") == "array" and "items" in node:
            return [self._process(node["items"])]

        properties = node.get("properties")
        if properties:
            result = {}
            for key, value in properties.items():
                self.current_path.append(key)
                if key == "marketplace_id":
                    result[key] = "%auto:marketplace_id%"
                elif key == "language_tag":
                    result[key] = "%auto:language%"
                elif key == "unit":
                    attr_code = self._compose_attr_code()
                    result[key] = f"%unit:{attr_code}%"
                else:
                    result[key] = self._process(value)
                self.current_path.pop()
            return result

        attr_code = self._compose_attr_code()
        return f"%value:{attr_code}%"

    def _compose_attr_code(self):
        keys = []
        for part in self.current_path:
            if part in {"value", "language_tag", "marketplace_id", "unit", "standardized_values"}:
                continue
            if part.endswith("_other_than_listed"):
                part = part.replace("_other_than_listed", "")
            keys.append(part)

        if not keys:
            return self.public_definition.code

        if keys[0] != self.public_definition.code:
            return "__".join([self.public_definition.code] + keys)

        return "__".join(keys)


class DefaultUnitConfiguratorFactory:
    """Create or update AmazonDefaultUnitConfigurator entries."""

    def __init__(self, public_definition, sales_channel, is_default=False):
        self.public_definition = public_definition
        self.sales_channel = sales_channel
        self.is_default = is_default

    def run(self):
        self._walk(self.public_definition.raw_schema or {}, [self.public_definition.code])

    def _compose_attr_code(self, path):
        keys = []
        for part in path:
            if part in {"value", "language_tag", "marketplace_id", "unit", "standardized_values"}:
                continue
            if part.endswith("_other_than_listed"):
                part = part.replace("_other_than_listed", "")
            keys.append(part)

        if not keys:
            return self.public_definition.code

        if keys[0] != self.public_definition.code:
            return "__".join([self.public_definition.code] + keys)

        return "__".join(keys)

    def _save_configurator(self, code, schema):
        enum = schema.get("enum") or []
        enum_names = schema.get("enumNames", enum)
        choices = [
            {"value": v, "name": n}
            for v, n in zip(enum, enum_names)
        ]

        configurator, created = AmazonDefaultUnitConfigurator.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            code=code,
            defaults={"name": schema.get("title", code)},
        )

        if created or self.is_default:
            configurator.name = schema.get("title", code)

        configurator.choices = choices
        configurator.save()

    def _walk(self, node, path):
        if not isinstance(node, dict):
            return

        if "items" in node and isinstance(node["items"], dict):
            self._walk(node["items"], path)
            return

        for key, val in node.get("properties", {}).items():
            path.append(key)
            if key == "unit":
                attr_code = self._compose_attr_code(path)
                self._save_configurator(attr_code, val)
                path.pop()
                continue

            self._walk(val, path)
            path.pop()
