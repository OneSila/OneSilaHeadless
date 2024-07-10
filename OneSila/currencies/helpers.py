import math
from decimal import Decimal


def roundup(x, ceil):
    ''' Roundup a number to the nearest ceiling
    For example:  roundup(111, 20) returns 120'''
    return int(math.ceil(x / Decimal(ceil))) * Decimal(ceil)


def currency_convert(round_prices_up_to, exchange_rate, price):
    '''
    Return converted currency price, rounded-up tot the nearest round_prices_up_to
    price = 100
    rate = 1.1
    return = 110
    '''
    if price is None:
        return None

    new_price = Decimal(price) * Decimal(exchange_rate)
    return roundup(new_price, round_prices_up_to)
