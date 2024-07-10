from core.tests import TestCase
from currencies.helpers import currency_convert


class CurrencyConvertTestCase(TestCase):
    def test_currency_convert_99(self):
        amount = 10
        new_acount = round(
            currency_convert(
                round_prices_up_to=.99,
                exchange_rate=1,
                price=10,
            ),
            2)
        expected_amount = 10.99
        self.assertEqual(new_acount, expected_amount)
