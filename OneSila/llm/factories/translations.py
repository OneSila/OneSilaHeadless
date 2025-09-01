from .mixins import AskGPTMixin, CalculateCostMixin, CreateTransactionMixin


class StringTranslationLLM(AskGPTMixin, CalculateCostMixin, CreateTransactionMixin):
    """
    Translate a given string from_language_code to a to_language_code
    The from_language_code is given for guardrails.
    """

    def __init__(self, to_translate, from_language_code, to_language_code, multi_tenant_company=None, sales_channel=None):
        super().__init__()
        self.to_translate = to_translate
        self.from_language_code = from_language_code
        self.to_language_code = to_language_code
        self.multi_tenant_company = multi_tenant_company
        self.sales_channel = sales_channel

    @property
    def system_prompt(self):
        return f"Translate from {self.from_language_code} to {self.to_language_code}.  Reply only with the translated text."

    @property
    def prompt(self):
        return f"{self.to_translate}"

    def translate(self):
        self.response = self.ask_gpt()
        self.calculate_cost(self.response)
        self.text_response = self.get_text_response(self.response)

        if self.multi_tenant_company:
            self._create_transaction()
            self._create_ai_translate_process()

        return self.text_response
