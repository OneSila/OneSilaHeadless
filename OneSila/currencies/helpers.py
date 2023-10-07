import math


def currency_convert(round_prices_up_to, exchange_rate, price):
    '''
    Return converted currency price, rounded-up tot the nearest round_prices_up_to
    price = 100
    rate = 1.1
    return = 110
    '''
    if price is None:
        new_price = None
    else:
        new_price = (price * exchange_rate)

    new_price = roundup(new_price, round_prices_up_to)

    return new_price


def roundup(x, ceil):
    ''' Roundup a number to the nearest ceiling
    For example:  roundup(111, 30) returns 120'''
    return int(math.ceil(x / float(ceil))) * ceil
