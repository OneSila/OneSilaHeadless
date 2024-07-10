from core.tests import TestCase
from currencies.helpers import currency_convert


class CurrencyConvertTestCase(TestCase):
    def test_currency_convert_dot_99(self):
        new_acount = float(round(
            currency_convert(
                round_prices_up_to=.99,
                exchange_rate=1,
                price=10,
            ),
            2))
        expected_amount = 10.99
        self.assertEqual(new_acount, expected_amount)

    def test_currency_convert_10_dot_5_to_dot_4(self):
        new_acount = float(round(
            currency_convert(
                round_prices_up_to=.4,
                exchange_rate=1,
                price=10.5,
            ),
            2))
        expected_amount = 11.4
        self.assertEqual(new_acount, expected_amount)

    def test_currency_convert_99(self):
        new_acount = float(round(
            currency_convert(
                round_prices_up_to=99,
                exchange_rate=1,
                price=10,
            ),
            2))
        expected_amount = 99.00
        self.assertEqual(new_acount, expected_amount)

    def test_currency_convert_9_dot_99(self):
        new_acount = float(round(
            currency_convert(
                round_prices_up_to=9.99,
                exchange_rate=1,
                price=8,
            ),
            2))
        expected_amount = 9.99
        self.assertEqual(new_acount, expected_amount)
