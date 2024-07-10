import math
from decimal import Decimal
def roundup(x, ceil):
    ''' Roundup a number to the nearest ceiling
    For example:  roundup(111, 20) returns 120
    If roundup < 1 we round up to the ceil itself
    '''
    ceil = Decimal(ceil)
    integral_part = int(x)
    fractional_part = x - integral_part

    if ceil < 1:
        if fractional_part < ceil:
            return Decimal(integral_part) + ceil
        else:
            return Decimal(integral_part) + 1 + ceil
    else:
        return Decimal(math.ceil(x / ceil) * ceil)



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
