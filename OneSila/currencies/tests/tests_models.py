from django.test import TestCase
from core.tests import TestCaseMixin
from model_bakery import baker
from currencies.models import Currency


class CurrencyTestCase(TestCaseMixin, TestCase):
    def test_blind_follow(self):
        currency_master = baker.make(Currency, is_default_currency=True, follow_official_rate=True)
        currency_slave = baker.make(Currency, is_default_currency=False, inherits_from=currency_master,
            follow_official_rate=True)
