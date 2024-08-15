from currencies.currencies import currencies
from currencies.models import Currency


class CreateDefaultCurrencyForMultiTenantCompanyFactory:
    def __init__(self, multi_tenant_company):
        self.multi_tenant_company = multi_tenant_company

    def set_currency_settings(self):
        currency = currencies.get(self.multi_tenant_company.country, None)

        if currency:
            currency['is_default_currency'] = True
            currency['multi_tenant_company'] = self.multi_tenant_company

        self.currency_settings = currency

    def populate_currency(self):
        if self.currency_settings:
            Currency.objects.create(**self.currency_settings)

    def run(self):
        self.set_currency_settings()
        self.populate_currency()
