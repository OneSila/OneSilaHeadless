from .mixins import AskGPTMixin, CalculateCostMixin, CreateTransactionMixin
import json

from ..models import AiImportProcess


class DetectPropertyTypeLLM(AskGPTMixin, CalculateCostMixin, CreateTransactionMixin):
    """
    Uses an LLM to detect the property type based on provided property data.
    """

    def __init__(self, property_data, multi_tenant_company=None):
        super().__init__()
        self.property_data = property_data
        self.multi_tenant_company = multi_tenant_company
        self.import_type = AiImportProcess.PROPERTY_TYPE_DETECTOR

    @property
    def system_prompt(self):
        return """
    # AI Assistant for Product Property Type Detection

    You are an AI assistant responsible for determining the correct product property type from a given JSON input. The input JSON may be in any language and includes one or both of the keys "name" and "internal_name". Your task is to analyze the provided property data and output exactly one word (in uppercase) representing the property type. Valid responses are:
      INT, FLOAT, TEXT, DESCRIPTION, BOOLEAN, DATE, DATETIME, SELECT, MULTISELECT.

    Below are guidelines and real-world examples for each type:

    1. **INT:**
       Use this for properties that are whole numbers.
       *Example:* A property representing "Warranty Period" (number of years) should be INT.

    2. **FLOAT:**
       Use this for properties that have decimal values.
       *Example:* A property representing "Weight" (which might be 1.5 or 2.75) should be FLOAT.

    3. **TEXT:**
       Use this for free-form, personalized text entries that are unique to the product and are not used for standard categorization.
       *Example:* A property like "Motto" or "Tagline"—a brief, unique phrase describing the product—should be TEXT.
       *Do NOT use TEXT for common product attributes such as material, model, or style.* This are SELECT when they can be common into multiple products.

    4. **DESCRIPTION:**
       Use this for longer, detailed descriptions.
       *Example:* A property representing "Product Description" that provides comprehensive details should be DESCRIPTION.

    5. **BOOLEAN:**
       Use this for properties representing a yes/no value.
       *Example:* A property like "Is Organic" should be BOOLEAN.

    6. **DATE:**
       Use this for properties that are simple dates.
       *Example:* A property like "Release Date" should be DATE.

    7. **DATETIME:**
       Use this for properties that include both date and time.
       *Example:* A property like "Manufacture DateTime" should be DATETIME.

    8. **SELECT:**
       Use this for properties that are single-choice selections. This is the most common type for product attributes.
       *Example:* A property like "Color", "Material", "Size", or "Brand" should be SELECT.

    9. **MULTISELECT:**
       Use this for properties that allow multiple selections from a predefined list.
       *Example:* A property like "Washing Instructions" should be MULTISELECT.

    Your response must be exactly one of these words (in uppercase) with no additional text or punctuation.
    """

    @property
    def prompt(self):
        return json.dumps(self.property_data, indent=2)

    def detect_type(self):
        """
        Uses the LLM to detect the property type.
        Returns the detected type as an uppercase, single word.
        """
        self.response = self.ask_gpt()
        self.calculate_cost(self.response)
        self.text_response = self.get_text_response(self.response).strip()
        self.detected_type = self.text_response.upper().split()[0]

        # Optionally, record the process if multi_tenant_company is provided.
        if self.multi_tenant_company:
            self._create_transaction()
            self._create_ai_import_process()

        return self.detected_type
