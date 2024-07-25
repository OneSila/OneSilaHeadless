from currencies.models import Currency

from currency_converter import CurrencyConverter
from django.db.models import F


class UpdateCurrencyPairMixin:
    def __init__(self):
        self.currency_converter = CurrencyConverter()

    def update_rate_pair(self, pair):
        from_iso = pair.inherits_from.iso_code
        to_iso = pair.iso_code
        pair.set_exchange_rate_official(self.currency_converter.convert(1, from_iso, to_iso))


class UpdateOfficialRateFactory(UpdateCurrencyPairMixin):
    """
    This factory will update the official-rate on every configured currency pair.
    """

    def set_base_currency_queryset(self):
        self.base_currency_queryset = Currency.objects.\
            filter(
                follow_official_rate=True,
                inherits_from__isnull=False
            )

    def update_all_rate_pairs(self):
        for pair in self.base_currency_queryset.iterator():
            self.update_rate_pair(pair)

    def run(self):
        self.set_base_currency_queryset()
        self.update_all_rate_pairs()


class UpdateSingleRate(UpdateCurrencyPairMixin):
    """
    This factory will update the normal rate if the currency is marked to follow_official_rate.
    """

    def __init__(self, currency):
        super().__init__()
        self.currency = currency

    def update_currency(self):
        if self.currency.follow_official_rate and self.currency.inherits_from:
            self.update_rate_pair(self.currency)

    def run(self):
        self.update_currency()
