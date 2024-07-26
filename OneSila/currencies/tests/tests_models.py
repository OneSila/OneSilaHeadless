from django.db.utils import IntegrityError
from core.tests import TestCase
from core.models import MultiTenantCompany
from model_bakery import baker
from currencies.models import Currency
from currencies.currencies import currencies


class CurrencyTestCase(TestCase):
    def test_blind_follow(self):
        currency_master, _ = Currency.objects.get_or_create(is_default_currency=True, follow_official_rate=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        currency_slave, _ = Currency.objects.get_or_create(is_default_currency=False, inherits_from=currency_master,
            follow_official_rate=True, multi_tenant_company=self.multi_tenant_company,
            **currencies['CA'])

    def test_currency_constraints(self):
        mtc = baker.make(MultiTenantCompany)
        mtc_bis = baker.make(MultiTenantCompany)

        currency_mtc, _ = Currency.objects.get_or_create(**currencies['GB'],
            is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc)

        try:
            currency_mtc_bis, _ = Currency.objects.get_or_create(**currencies['US'],
                is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc_bis)
        except IntegrityError:
            self.fail("You should be able to have a default currency for every multi_tenant_company")
            raise

        try:
            currency_mtc_two, _ = Currency.objects.get_or_create(
                **currencies['PL'],
                is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc)
            self.fail("You should not be able to create two default currencies under the same multi_tenant_company")
        except IntegrityError:
            pass
