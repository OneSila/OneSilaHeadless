from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator, \
    PrivateStructuredDataGenerator
from currencies.models import Currency
from currencies.currencies import currencies

registry = DemoDataLibrary()


@registry.register_private_app
class CurrencyDefaultDataGenerator(PrivateStructuredDataGenerator):
    model = Currency

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "is_default_currency": True,
                },
                'post_data': {
                    "iso_code": "GBP",
                    "comment": "Base Currency",
                    "name": "British Pound",
                    "symbol": "£",
                },
            },
        ]


    def preflight_check(self, pre_kwargs):
        is_default_currency = pre_kwargs.get('is_default_currency')
        if is_default_currency and Currency.objects.filter(is_default_currency=is_default_currency, multi_tenant_company=self.multi_tenant_company).exists():
            return False

        return True


@registry.register_private_app
class CurrencyNonDefaultDataGenerator(PrivateStructuredDataGenerator):
    model = Currency

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "is_default_currency": False,
                    "iso_code": "USD",
                    "comment": "USD following Base Currency",
                    "name": "American Dollar",
                    "symbol": "$",
                    "inherits_from": Currency.objects.get(multi_tenant_company=self.multi_tenant_company, is_default_currency=True),
                    "follow_official_rate": True,
                    "exchange_rate_official": 1.13,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "is_default_currency": False,
                    "iso_code": "EUR",
                    "comment": "EUR following Base Currency",
                    "name": "Euro",
                    "symbol": "€",
                    "inherits_from": Currency.objects.get(multi_tenant_company=self.multi_tenant_company, is_default_currency=True),
                    "follow_official_rate": False,
                    "exchange_rate": 1.1,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "is_default_currency": False,
                    "iso_code": "THB",
                    "comment": "Thai Baht not following",
                    "name": "Thai Baht",
                    "symbol": "฿",
                    "inherits_from": None,
                    "follow_official_rate": False,
                    "exchange_rate": 1.1,
                },
                'post_data': {},
            },
        ]
