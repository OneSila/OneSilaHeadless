from sales_prices.factories import SalesPriceUpdateCreateFactory, \
    SalesPriceCreateForCurrencyFactory


def salesprice_updatecreate_flow(sales_price):
    f = SalesPriceUpdateCreateFactory(sales_price)
    f.run()


def salesprice_create_for_currency_flow(currency):
    f = SalesPriceCreateForCurrencyFactory(currency)
    f.run()
