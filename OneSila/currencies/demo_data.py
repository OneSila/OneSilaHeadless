from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from currencies.models import Currency


registry = DemoDataLibrary()


@registry.register_private_app
def currencies_create_currency_structure(multi_tenant_company):
    """We want to create a basic currency structure to ensure we are able to show how the app works."""

    # Create first, the base currency:
    base_currency, created = Currency.objects.get_or_create(multi_tenant_company=multi_tenant_company, iso_code="GBP")

    if created:
        base_currency.is_default_currency = not Currency.objects.filter(multi_tenant_company=multi_tenant_company, is_default_currency=True).exists()
        base_currency.comment = "Base Currency"
        base_currency.name = "British Pound"
        base_currency.symbol = "£"
        base_currency.save()

    registry.create_demo_data_relation(base_currency)

    # Once done, let's create an automated currency from the USD
    usd_currency, created = Currency.objects.get_or_create(
        multi_tenant_company=multi_tenant_company,
        iso_code="USD"
    )

    if created:
        usd_currency.name = "American Dollar"
        usd_currency.symbol = "$"
        usd_currency.is_default_currency = False
        usd_currency.inherits_from = base_currency
        usd_currency.follow_official_rate = True
        usd_currency.exchange_rate_official = 1.13
        usd_currency.comment = "Auto-following official rate"
        usd_currency.save()

    registry.create_demo_data_relation(usd_currency)

    # Let's create an automated currency using our own rates
    eur_currency, created = Currency.objects.get_or_create(
        multi_tenant_company=multi_tenant_company,
        iso_code="EUR"
    )

    if created:
        eur_currency.name = "Euro"
        eur_currency.symbol = "€"
        eur_currency.is_default_currency = False
        eur_currency.inherits_from = base_currency
        eur_currency.follow_official_rate = False
        eur_currency.exchange_rate = 1.1
        eur_currency.comment = "Auto-following manual rate"
        eur_currency.save()

    registry.create_demo_data_relation(eur_currency)

    # Let's create a manual currency not following any rates.
    thb_currency, created = Currency.objects.get_or_create(
        multi_tenant_company=multi_tenant_company,
        iso_code="THB"
    )

    if created:
        thb_currency.name = "Thai Baht"
        thb_currency.symbol = "฿"
        thb_currency.is_default_currency = False
        thb_currency.comment = "None following"
        thb_currency.save()

    registry.create_demo_data_relation(thb_currency)
