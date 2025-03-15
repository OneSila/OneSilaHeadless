from .mixins import AskGPTMixin


class StringTranslationLLM(AskGPTMixin):
    """
    Translate a given string from_language_code to a to_language_code
    The from_language_code is given for guardrails. 
    """
    def __init__(self, to_translate, from_language_code, to_language_code):
        super().__init__()
        self.to_translate = to_translate
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code

    @property    
    def system_prompt(self):
        return f"Translate from {self.from_language_code} to {self.to_language_code}.  Reply only with the translated text."

    @property
    def prompt(self):
        return f"{self.to_translate}"