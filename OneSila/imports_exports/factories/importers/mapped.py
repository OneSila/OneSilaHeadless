import json
import mimetypes
import requests
from django.core.exceptions import ValidationError
from imports_exports.factories.imports import ImportMixin
from imports_exports.models import MappedImport, TypedImport


class MappedImportRunner(ImportMixin):
    def __init__(self, import_process: MappedImport):

        # Set flags based on type
        self.import_properties = import_process.type == TypedImport.TYPE_PROPERTY
        self.import_select_values = import_process.type == TypedImport.TYPE_PROPERTY_SELECT_VALUE
        self.import_rules = import_process.type == TypedImport.TYPE_PROPERTY_RULE
        self.import_products = import_process.type == TypedImport.TYPE_PRODUCT

        self.data = None

        super().__init__(import_process, language=import_process.language)

    def prepare_import_process(self):
        """
        Validate and load the JSON content into `self.data`.
        """

        if self.import_process.json_file:
            if not self.import_process.json_file.name.lower().endswith('.json'):
                raise ValidationError("Uploaded file is not a JSON file.")

            mime_type, _ = mimetypes.guess_type(self.import_process.json_file.name)
            if mime_type not in ['application/json', 'text/plain']:
                raise ValidationError("File MIME type is not recognized as JSON.")

            try:
                with self.import_process.json_file.open('r', encoding='utf-8') as f:
                    self.data = json.load(f)

            except json.JSONDecodeError:
                raise ValidationError("Uploaded file is not valid JSON.")

        elif self.import_process.json_url:
            if not self.import_process.json_url.lower().endswith('.json'):
                raise ValidationError("URL does not point to a .json resource.")

            try:
                response = requests.get(self.import_process.json_url, timeout=10)
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    raise ValidationError(f"URL content-type is not JSON: {content_type}")

                self.data = response.json()

            except requests.RequestException as e:
                raise ValidationError(f"Failed to fetch remote JSON: {e}")
            except json.JSONDecodeError:
                raise ValidationError("Remote content is not valid JSON.")

        else:
            raise ValidationError("No input source provided for mapped import.")

    def get_total_instances(self):
        if isinstance(self.data, dict):
            return 1
        return len(self.data)

    # --------------
    # PRODUCT
    # --------------
    def get_products_data(self):
        return [self.data] if self.get_total_instances() == 1 else self.data

    def get_structured_product_data(self, product_data):
        return product_data

    # --------------
    # PROPERTY
    # --------------
    def get_properties_data(self):
        return [self.data] if self.get_total_instances() == 1 else self.data

    def get_structured_property_data(self, property_data):
        return property_data

    # --------------
    # SELECT VALUES
    # --------------
    def get_select_values_data(self):
        return [self.data] if self.get_total_instances() == 1 else self.data

    def get_structured_select_value_data(self, value_data):
        return value_data

    # --------------
    # RULES
    # --------------
    def get_rules_data(self):
        return [self.data] if self.get_total_instances() == 1 else self.data

    def get_structured_rule_data(self, rule_data):
        return rule_data
