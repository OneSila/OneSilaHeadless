from currencies.factories.default_currency import CreateDefaultCurrencyForMultiTenantCompanyFactory


class CreateDefaultCurrencyForMultiTenantCompanyFlow:
    def __init__(self, multi_tenant_company):
        self.factory = CreateDefaultCurrencyForMultiTenantCompanyFactory(multi_tenant_company)

    def flow(self):
        self.factory.run()
