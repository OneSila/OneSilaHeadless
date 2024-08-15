from sales_prices.factories import SalesPriceCurrencyChangeFactory


def salesprice_currency_change_flow(currency):
    f = SalesPriceCurrencyChangeFactory(currency)
    f.run()
