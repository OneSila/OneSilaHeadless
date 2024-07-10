from sales_prices.factories import SalesPriceUpdateCreateFactory


def salesprice_updatecreate_flow(sales_price):
    f = SalesPriceUpdateCreateFactory(sales_price)
    f.run()
