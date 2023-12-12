from currencies.models import Currency

from currency_converter import CurrencyConverter
from django.db.models import F


class UpdateOfficialRateFactory:
    """
    This factory will update the officel-rate on every currency.
    """

    def set_currency_queryset(self):
        self.currency_queryset = Currency.objects.\
            all().\
            alias(from_iso=F('inherits_from__iso_code')),
        alias(to_iso=F('iso_code')),

    def set_currency_pairs(self):
        """
        Find all currency pairs, from_currency, to_currency
        """
        self.currency_pairs = Currency.objects.\
            values_list('from_iso', 'to_iso').\
            distinct()

    def filter_currency_pair_instances(self, pair):
        return self.currency_queryset.filter(from_iso=pair.from_iso, to_iso=pair.to_iso)

    def update_rate_pair(self, pair):
        new_rate = CurrencyConverter(pair.from_iso, pair.to_iso)
        to_update = self.filter_currency_pair_instances(pair)

        for i in to_update:
            i.set_exchange_rate_official(new_rate)

    def update_all_rate_pairs(self):
        for pair in self.currency_pairs:
            self.update_rate_pair(pair)

    def run(self):
        self.set_currency_queryset()
        self.set_currency_pairs()
        self.update_all_rate_pairs()


class FollowerRateFactory:
    """
    This factory will update the normal rate if the currency is marked to follow_official_rate.
    """

    def __init__(self, currency):
        self.currency = currency

    def update_currency(self):
        if self.currency.follow_official_rate:
            self.currency.exchange_rate = self.currency.exchange_rate_official
            self.currency.save()

    def run(self):
        self.update_currency()
