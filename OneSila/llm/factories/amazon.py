from .mixins import OpenAIMixin


class AmazonSelectValueTranslationLLM(OpenAIMixin):
    """Translate Amazon property select values using OpenAI."""
    model = "gpt-4.1-nano"
    temperature = 0.3
    max_tokens = 300

    def __init__(self, remote_name, from_language_code="auto", to_language_code="en", property_name=None, property_code=None):
        super().__init__()
        self.remote_name = remote_name
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.property_name = property_name
        self.property_code = property_code

    @property
    def system_prompt(self):
        return (
            "You are translating e-commerce property values. "
            "Do not translate product codes, model numbers, color codes, or other alphanumeric identifiers. "
            "If the input appears to be such a code, return the string exactly as it was provided. "
            "If you are less than 90% confident in the translation, return the original value. Output only the final value."
        )

    @property
    def prompt(self):
        context_line = ""
        if self.property_name and self.property_code:
            context_line = (
                f"This value belongs to the amazon product attribute: '{self.property_name}' (code: {self.property_code}).\n"
            )
        return (
            f"{context_line}"
            f"Translate the following Amazon property select value from {self.from_language_code} to {self.to_language_code}:\n"
            f"{self.remote_name}\n\n"
            "Rules:\n"
            "- Do not translate product codes, model numbers, color codes, or any alphanumeric values; output the input exactly as provided.\n"
            "- Only translate if you are at least 90% confident the translation is correct; otherwise return the original value.\n"
            "Respond with only the final value, no extra text, no explanation, no punctuation. "
            "Just one word or phrase. If the value is numeric or contains numbers, keep the numbers as digits."
        )

    def translate(self):
        response = self.openai.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self.prompt}
                    ]
                }
            ],
        )
        return response.output[0].content[0].text.strip()
