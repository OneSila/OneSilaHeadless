from .mixins import OpenAIMixin


class AmazonSelectValueTranslationLLM(OpenAIMixin):
    """Translate Amazon property select values using OpenAI."""
    model = "gpt-4.1-nano"
    temperature = 0.3
    max_tokens = 20

    def __init__(self, remote_value, from_language_code="auto", to_language_code="en", property_name=None, property_code=None):
        super().__init__()
        self.remote_value = remote_value
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.property_name = property_name
        self.property_code = property_code

    @property
    def system_prompt(self):
        return "You are translating e-commerce property values. Output only the translated value."

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
            f"{self.remote_value}\n\n"
            "Only respond with the translated value, no extra text, no explanation, no punctuation. "
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
