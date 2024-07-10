from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from currencies.models import Currency


registry = DemoDataLibrary()


@registry.register_private_app
def currencies_create_currency_structure(multi_tenant_company):
    """We want to create a basic currency structure to ensure we are able to show how the app works."""

    # Create first, the base currency:
    base_currency = Currency.objects.create(multi_tenant_company=multi_tenant_company,
        iso_code="GBP",
        name="British Pound",
        symbol="£",
        is_default_currency=not Currency.objects.filter(multi_tenant_company=multi_tenant_company, is_default_currency=True).exists(),
        comment="Base Currency")

    registry.create_demo_data_relation(base_currency)

    # Once done, let's create an automated currency from the USD
    currency = Currency.objects.create(multi_tenant_company=multi_tenant_company,
        iso_code="USD",
        name="American Dollar",
        symbol="$",
        is_default_currency=False,
        inherits_from=base_currency,
        follow_official_rate=True,
        exchange_rate_official=1.13,
        comment="Auto-following official rate")
    registry.create_demo_data_relation(currency)

    # Let's create an automated currency using our own rates
    currency = Currency.objects.create(multi_tenant_company=multi_tenant_company,
        iso_code="EUR",
        name="Euro",
        symbol="€",
        is_default_currency=False,
        inherits_from=base_currency,
        follow_official_rate=False,
        exchange_rate=1.1,
        comment="Auto-following manuel rate")
    registry.create_demo_data_relation(currency)

    # Let's create an manual currency not following any rates.
    currency = Currency.objects.create(multi_tenant_company=multi_tenant_company,
        iso_code="THB",
        name="Thai Baht",
        symbol="฿",
        is_default_currency=False,
        comment="None following")
    registry.create_demo_data_relation(currency)
