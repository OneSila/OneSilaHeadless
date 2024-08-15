from core.tests import TestCase

from currencies.models import Currency
from currencies.currencies import currencies
from currencies.flows import update_single_rate_flow, update_rate_flow

from currency_converter import CurrencyConverter


class UpdateRatesTestCase(TestCase):
    def convert(self, from_iso, to_iso):
        conv = CurrencyConverter()
        return conv.convert(1, from_iso, to_iso)

    def test_update_official_rates(self):
        currency_base, _ = Currency.objects.get_or_create(is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])

        currency_follow, _ = Currency.objects.get_or_create(is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency_base,
            follow_official_rate=True,
            **currencies['BE'])

        fake_rate = 10000000
        currency_not_follow, _ = Currency.objects.get_or_create(is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency_base,
            follow_official_rate=False,
            exchange_rate=fake_rate,
            **currencies['BG'])

        update_rate_flow()
        currency_not_follow = Currency.objects.get(id=currency_not_follow.id)
        currency_follow = Currency.objects.get(id=currency_follow.id)

        rate_follow_expected = self.convert(currency_base.iso_code, currency_follow.iso_code)
        self.assertEqual(rate_follow_expected, currency_follow.rate)
        self.assertEqual(fake_rate, currency_not_follow.rate)

    def test_update_single_rate(self):
        currency_base, _ = Currency.objects.get_or_create(is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])

        fake_rate = 1212121
        currency_new, _ = Currency.objects.get_or_create(is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency_base,
            follow_official_rate=True,
            exchange_rate_official=fake_rate,
            **currencies['SE'])

        update_single_rate_flow(currency_new)
        currency_new = Currency.objects.get(id=currency_new.id)

        rate_follow_expected = self.convert(currency_base.iso_code, currency_new.iso_code)
        self.assertEqual(rate_follow_expected, currency_new.rate)
