from django.db.utils import IntegrityError
from core.tests import TestCase
from core.models import MultiTenantCompany
from model_bakery import baker
from currencies.models import Currency


class CurrencyTestCase(TestCase):
    def test_blind_follow(self):
        currency_master = baker.make(Currency, is_default_currency=True, follow_official_rate=True)
        currency_slave = baker.make(Currency, is_default_currency=False, inherits_from=currency_master,
            follow_official_rate=True)

    def test_currency_constraints(self):
        mtc = baker.make(MultiTenantCompany)
        mtc_bis = baker.make(MultiTenantCompany)

        currency_mtc = baker.make(Currency, iso_code="GBP", is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc)

        try:
            currency_mtc_bis = baker.make(Currency, iso_code="GBP", is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc_bis)
        except IntegrityError:
            self.fail("You should be able to have a default currency for every multi_tenant_company")
            raise

        try:
            currency_mtc_two = baker.make(Currency, iso_code="EUR", is_default_currency=True, follow_official_rate=True, multi_tenant_company=mtc)
            self.fail("You should not be able to create two default currencies under the same multi_tenant_company")
        except IntegrityError:
            pass
