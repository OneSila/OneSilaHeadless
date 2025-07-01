from spapi import DefinitionsApi

from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.decorators import throttle_safe
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, PullAmazonMixin
from sales_channels.integrations.amazon.models import AmazonSalesChannelView
from sales_channels.integrations.amazon.models.properties import AmazonProductType, AmazonPublicDefinition, \
    AmazonProperty, AmazonPropertySelectValue, AmazonProductTypeItem
import requests

from properties.models import ProductPropertiesRuleItem, Property
from sales_channels.integrations.amazon.constants import AMAZON_LOCALE_MAPPING, AMAZON_INTERNAL_PROPERTIES
from sales_channels.integrations.amazon.decorators import throttle_safe
from django.utils import timezone


def _resolve_property_type(existing_type: str, new_type: str) -> str:
    """Return the most permissive property type based on the rules provided."""
    if existing_type == new_type:
        return existing_type

    if Property.TYPES.MULTISELECT in {existing_type, new_type}:
        return Property.TYPES.MULTISELECT

    if Property.TYPES.SELECT in {existing_type, new_type}:
        return Property.TYPES.SELECT

    if {existing_type, new_type} <= {Property.TYPES.TEXT, Property.TYPES.DESCRIPTION}:
        return Property.TYPES.DESCRIPTION

    if Property.TYPES.DATETIME in {existing_type, new_type} and Property.TYPES.DATE in {existing_type, new_type}:
        return Property.TYPES.DATETIME

    if Property.TYPES.FLOAT in {existing_type, new_type} and Property.TYPES.INT in {existing_type, new_type}:
        return Property.TYPES.FLOAT

    return existing_type

class AmazonFullSchemaPullFactory(GetAmazonAPIMixin, PullAmazonMixin, PullRemoteInstanceMixin):
    """
    Pull factory to synchronize Amazon product types, items, properties, and select values.
    Main model: AmazonProductType, using category_code from get_product_types.
    """

    remote_model_class = AmazonProductType
    field_mapping = {
        'product_type_code': 'product_type_code',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['product_type_code', 'sales_channel']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        """
        Fetch product types from Amazon's SP-API using get_product_types.
        """
        product_types = self.get_product_types()
        self.remote_instances = [
            {
                'product_type_code': pt,
            }
            for pt in product_types
        ]


    def _download_json(self, url, category_code=None, marketplace_id=None):
        """
        Download the JSON schema from Amazon's URL and save it to disk for inspection.
        """
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data

    @throttle_safe(max_retries=5, base_delay=1)
    def _get_schema_for_marketplace(self, view, category_code, is_default_marketplace=False):
        """
        SP-API call to get product type definition for a given marketplace view.
        Returns parsed schema JSON with optional title added.
        """
        definitions_api = DefinitionsApi(self._get_client())
        response = definitions_api.get_definitions_product_type(
            product_type=category_code,
            marketplace_ids=[view.remote_id],
            requirements="LISTING",
            seller_id=self.sales_channel.remote_id,
        )

        schema_link = response.var_schema.link.resource
        schema_data = self._download_json(schema_link)

        if is_default_marketplace:
            schema_data["title"] = response.display_name

        return schema_data


    def post_pull_action(self):
        """
        After pulling the product types, resolve their attributes via schema fetch + public def sync.
        """
        sales_channel_views = AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
        product_types = AmazonProductType.objects.filter(
            sales_channel=self.sales_channel,
            product_type_code__in=[pt['product_type_code'] for pt in self.remote_instances]
        )

        for product_type in product_types:

            # Step 1: Get schemas for all marketplaces
            for view in sales_channel_views:
                lang = view.remote_languages.first()
                is_default = lang and self.sales_channel.country and self.sales_channel.country in lang.remote_code

                schema_data = self._get_schema_for_marketplace(view, product_type.product_type_code, is_default_marketplace=is_default)
                required_properties = schema_data["required"]

                if is_default:
                    # create AmazonProductType the schema_data will have a title
                    product_type.name = schema_data['title']
                    product_type.save()

                properties = schema_data.get("properties", {})
                for code, schema in properties.items():
                    # create AmazonPublicDefinition we will have the thing from the view or instead we can just use the amazon domain thing like Amazon.nl or something that comes from the schema
                    # public_definition = self.get_or_create_public_definition(...)
                    # enrich public_definition with export_definition and ussage_definition
                    # then do get or create for remote items, remote property and remote select values based on public_definition.export_definition
                    # OR
                    # the first public definition like "battery" will have export_definitions as an array with all the needed things that needs created
                    # but we still need to create the public definitions for all of that as well.
                    # if schema is_internal we will not do the export_definition and ussage_definition
                    public_definition = self.sync_public_definitions(code, schema, required_properties, product_type, view)

                    if public_definition.is_internal:
                        continue

                    self.create_remote_properties(public_definition, product_type, view, is_default)

    def sync_public_definitions(self, attr_code, schema_definition, required_properties, product_type_obj, view):
        """
        Go over the parsed schema_definition and sync AmazonPublicDefinition models.
        """

        public_def, created = AmazonPublicDefinition.objects.get_or_create(
            product_type_code=product_type_obj.product_type_code,
            api_region_code=view.api_region_code,
            code=attr_code,
        )

        public_def.name = schema_definition["title"] if "title" in schema_definition else f"{attr_code} {view.api_region_code}"
        public_def.raw_schema = schema_definition
        public_def.is_required = attr_code in required_properties
        public_def.is_internal = attr_code in AMAZON_INTERNAL_PROPERTIES
        public_def.save()


        if public_def.should_refresh() and not public_def.is_internal:

            # These factories will handle smart fallback logic (for now: pass)
            export_definition_fac = ExportDefinitionFactory(public_def)
            export_definition_fac.run()

            # UsageDefinitionFactory(public_def).run()
            public_def.export_definition = export_definition_fac.results
            public_def.last_fetched = timezone.now()
            public_def.save()

        return public_def

    def create_remote_properties(self, public_definition, product_type, view, is_default):

        for property_data in public_definition.export_definition:

            remote_property, created = AmazonProperty.objects.get_or_create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                code=property_data['code'],
                defaults={'type': property_data['type']},
            )

            allows_unmapped_values = property_data.get('allows_unmapped_values', False)

            if not created:
                old_type = remote_property.type
                resolved_type = _resolve_property_type(old_type, property_data['type'])
                if resolved_type != remote_property.type:
                    remote_property.type = resolved_type
                if resolved_type == Property.TYPES.SELECT and (
                    old_type in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION] or
                    property_data['type'] in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION]
                ):
                    remote_property.allows_unmapped_values = True
                if allows_unmapped_values:
                    remote_property.allows_unmapped_values = True
            else:
                remote_property.name = property_data['name']
                remote_property.allows_unmapped_values = allows_unmapped_values

            if is_default:
                remote_property.name = property_data['name']

            remote_property.save()

            if remote_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
                for value in property_data['values']:
                    remote_select_value, _ = AmazonPropertySelectValue.objects.get_or_create(
                        multi_tenant_company=self.sales_channel.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        marketplace=view,
                        amazon_property=remote_property,
                        remote_value=value['value'],
                    )

                    remote_select_value.remote_name = value['name']
                    remote_select_value.save()

                remote_rule_item, created_item = AmazonProductTypeItem.objects.get_or_create(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    amazon_rule=product_type,
                    remote_property=remote_property
                )

                new_type = (
                    ProductPropertiesRuleItem.REQUIRED
                    if public_definition.is_required
                    else ProductPropertiesRuleItem.OPTIONAL
                )

                if (
                    created or
                    (remote_rule_item.remote_type == ProductPropertiesRuleItem.OPTIONAL and new_type == ProductPropertiesRuleItem.REQUIRED)
                ):
                    remote_rule_item.remote_type = new_type
                    remote_rule_item.save()



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

    def run(self):
        # TODO: define how to render values into expected Amazon SP-API format
        pass
