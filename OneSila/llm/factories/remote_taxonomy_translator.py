from .mixins import OpenAIMixin


class RemoteSelectValueTranslationLLM(OpenAIMixin):
    """Translate remote property select values using OpenAI."""

    model = "gpt-4.1-nano"
    temperature = 0.3
    max_tokens = 300

    def __init__(
        self,
        *,
        integration_label: str,
        remote_name: str,
        from_language_code: str = "auto",
        to_language_code: str = "en",
        property_name: str | None = None,
        property_code: str | None = None,
    ) -> None:
        super().__init__()
        self.integration_label = integration_label
        self.remote_name = remote_name
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.property_name = property_name
        self.property_code = property_code

    @property
    def system_prompt(self) -> str:
        return (
            "You are translating e-commerce property values. "
            "Do not translate product codes, model numbers, color codes, or other alphanumeric identifiers. "
            "If the input appears to be such a code, return the string exactly as it was provided. "
            "If you are less than 90% confident in the translation, return the original value. Output only the final value."
        )

    @property
    def prompt(self) -> str:
        context_line = ""
        if self.property_name and self.property_code:
            context_line = (
                f"This value belongs to the {self.integration_label} product attribute: "
                f"'{self.property_name}' (code: {self.property_code}).\n"
            )
        elif self.property_name:
            context_line = (
                f"This value belongs to the {self.integration_label} product attribute named "
                f"'{self.property_name}'.\n"
            )
        elif self.property_code:
            context_line = (
                f"This value belongs to the {self.integration_label} product attribute with code "
                f"'{self.property_code}'.\n"
            )

        return (
            f"{context_line}"
            f"Translate the following {self.integration_label} property select value from "
            f"{self.from_language_code} to {self.to_language_code}:\n"
            f"{self.remote_name}\n\n"
            "Rules:\n"
            "- Do not translate product codes, model numbers, color codes, or any alphanumeric values; "
            "output the input exactly as provided.\n"
            "- Only translate if you are at least 90% confident the translation is correct; otherwise return "
            "the original value.\n"
            "Respond with only the final value, no extra text, no explanation, no punctuation. "
            "Just one word or phrase. If the value is numeric or contains numbers, keep the numbers as digits."
        )

    def translate(self) -> str:
        response = self.openai.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self.prompt},
                    ],
                }
            ],
        )
        return response.output[0].content[0].text.strip()


class RemotePropertyTranslationLLM(OpenAIMixin):
    """Translate remote property names using OpenAI."""

    model = "gpt-4.1-nano"
    temperature = 0.3
    max_tokens = 300

    def __init__(
        self,
        *,
        integration_label: str,
        remote_name: str,
        from_language_code: str = "auto",
        to_language_code: str = "en",
        remote_identifier: str | None = None,
    ) -> None:
        super().__init__()
        self.integration_label = integration_label
        self.remote_name = remote_name
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.remote_identifier = remote_identifier

    @property
    def system_prompt(self) -> str:
        return (
            "You are translating e-commerce property names. "
            "Do not translate product codes, model numbers, or other alphanumeric identifiers. "
            "If the input appears to be such a code, return it exactly as provided. "
            "If you are less than 90% confident in the translation, return the original value. Output only the final value."
        )

    @property
    def prompt(self) -> str:
        identifier_line = ""
        if self.remote_identifier:
            identifier_line = (
                f"This property has the identifier '{self.remote_identifier}' in {self.integration_label}.\n"
            )

        return (
            f"{identifier_line}"
            f"Translate the following {self.integration_label} property name from {self.from_language_code} "
            f"to {self.to_language_code}:\n"
            f"{self.remote_name}\n\n"
            "Rules:\n"
            "- Preserve any product codes, model numbers, or alphanumeric identifiers exactly as provided.\n"
            "- Only translate if you are at least 90% confident the translation is correct; otherwise return "
            "the original value.\n"
            "Respond with only the final name, without explanations or additional text."
        )

    def translate(self) -> str:
        response = self.openai.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self.prompt},
                    ],
                }
            ],
        )
        return response.output[0].content[0].text.strip()
