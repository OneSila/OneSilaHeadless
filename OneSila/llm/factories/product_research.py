from .mixins import AskGPTMixin


class ProductResearchLLM(AskGPTMixin):
    """
    Translate a given string from_language_code to a to_language_code
    The from_language_code is given for guardrails.
    """

    def __init__(self, product_name):
        super().__init__()
        self.product_name = product_name

    @property
    def system_prompt(self):
        return """
        # **High-Quality Product Research Prompt (JSON Format)**

        I need a **structured JSON response** with real, verifiable, and up-to-date product information sourced from **authoritative online sources**.
        🚫 **No generated or fabricated data. Only return what is available.**

        ## **🔍 Data Requirements**
        - **Source data from reputable online platforms** (official manufacturer websites, major e-commerce platforms like Amazon, Walmart, Best Buy, etc.).
        - **Strict adherence to JSON format** as defined below.
        - **If any field is unavailable, return `null` instead of making assumptions.**

        ## **🛒 Expected JSON Output Format**
        ```json
        {
          "product_name": "string",
          "description": "string",
          "images": [
            "image_url_1",
            "image_url_2",
            "image_url_N"
          ],
          "attributes": {
            "key1": "value1",
            "key2": "value2",
            "keyN": "valueN"
          }
        }
        ```

        ---

        ## **📌 Data Extraction Guidelines**
        ### **1️⃣ Product Name**
        - Extract the **exact name** from official sources or leading e-commerce platforms.
        - Do **not** modify or shorten the name.

        ### **2️⃣ Description**
        - Use the **official** product description from the manufacturer or primary retailer.
        - No summarization or generation—**maintain full accuracy.**

        ### **3️⃣ Images**
        - Extract only **high-quality product images** from **official sources or trusted retailers**.
        - Return **direct image URLs**; do not modify or generate images.

        ### **4️⃣ Attributes**
        - Extract all relevant **technical specifications** (e.g., size, weight, material, color, model number, power, etc.).
        - Ensure **attributes match manufacturer or retailer listings.**

        ### **5️⃣ Data Integrity**
        ✅ **Only use real, verified data.**
        🚫 **Do not fabricate or assume information.**
        🔄 **If data is unavailable, return `null` instead of guessing.**

        """

    @property
    def prompt(self):
        return f"{self.product_name}"
