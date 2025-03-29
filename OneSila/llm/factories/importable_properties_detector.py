import json
from .mixins import AskGPTMixin, CalculateCostMixin, CreateTransactionMixin
from ..models import AiImportProcess


class DetectRealProductAttributesLLM(AskGPTMixin, CalculateCostMixin, CreateTransactionMixin):
    """
    Uses an LLM to detect which product attributes are real importable product properties.
    """

    def __init__(self, attributes_data, integration_name, multi_tenant_company=None, extra_instructions=None):
        super().__init__()
        self.attributes_data = attributes_data  # Should be a list of dicts with "label", and optional "extra_info"
        self.integration_name = integration_name  # e.g., "Magento", "Shopify"
        self.multi_tenant_company = multi_tenant_company
        self.extra_instructions = extra_instructions
        self.import_type = AiImportProcess.IMPORTABLE_PROPERTIES_DETECTOR

    @property
    def system_prompt(self):
        return """
            You are an AI assistant for a Product Information Management (PIM) system.
            
            You are given a list of product attributes. Each attribute has:
            - a `label` (string) — the name of the attribute
            - optional `extra_info` — a dictionary with additional metadata about the attribute
            - an `index` — the attribute’s position in the original list
            
            Your task is to determine which of these attributes should be imported into the PIM system.
            
            Only mark an attribute for import if it describes **real, customer-relevant, product-specific information**, such as:
            
            - Physical characteristics (e.g. Width, Size, Seat Depth, Weight)
            - Visual characteristics (e.g. Color, Material, Design)
            - Origin and branding (e.g. Brand, Manufacturer, Country of Origin)
            - Functional or distinguishing traits (e.g. Organic, Expiration Date, Number of Seats)
            
            Do **not** import:
            - System/internal attributes (e.g. IDs, SKUs, layout options, technical flags, product name)
            - Pricing and stock info (e.g. Price, Cost, Quantity, Enable/Disable)
            - Meta or SEO fields (e.g. Meta Title, URL Key)
            - Media/image-only fields (e.g. Base Image, Gallery, Thumbnail)
            
            ### Output:
            Return a **JSON array** like this:
            
            [
              {
                "index": <index>,
                "label": "<label>",
                "imported": true | false
              }
            ]
        """.strip()

    @property
    def prompt(self):
        # Build a clean prompt with index, label and optional extra_info
        processed_attributes = []

        for idx, attr in enumerate(self.attributes_data):
            processed = {
                "index": idx,
                "label": attr.get("label")
            }
            if "extra_info" in attr:
                processed["extra_info"] = attr["extra_info"]
            processed_attributes.append(processed)

        full_prompt = {
            "integration": self.integration_name,
            "attributes": processed_attributes
        }

        if self.extra_instructions:
            full_prompt["extra_instructions"] = self.extra_instructions

        return json.dumps(full_prompt, indent=2)

    def clean_json_response(self, text):
        clean = text.strip()

        # Remove triple backticks block (start and end)
        if clean.startswith("```"):
            clean = clean.split("```", 1)[1].strip()  # remove opening ```, maybe with `json`
            if clean.startswith("json"):
                clean = clean[len("json"):].strip()
            if "```" in clean:
                clean = clean.split("```")[0].strip()  # remove closing ```

        return json.loads(clean)

    def detect_attributes(self):
        """
        Uses the LLM to determine which attributes to import.
        Returns a list of {index: int, imported: bool} objects.
        """
        self.response = self.ask_gpt()
        self.calculate_cost(self.response)
        self.text_response = self.get_text_response(self.response)
        self.detected = self.clean_json_response(self.text_response)

        if self.multi_tenant_company:
            self._create_transaction()
            self._create_ai_import_process()

        return self.detected
