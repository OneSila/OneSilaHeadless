def sales_price__salespricelistitem__create_update_flow(sales_price):
    from sales_prices.factories import SalesPriceForSalesPriceListItemCreateFactory
    f = SalesPriceForSalesPriceListItemCreateFactory(sales_price=sales_price)
    f.run()


def sales_price_list__salespricelistitem__create_update_flow(salespricelist):
    from sales_prices.factories import SalesPriceListForSalesPriceListItemsCreateUpdateFactory
    f = SalesPriceListForSalesPriceListItemsCreateUpdateFactory(salespricelist=salespricelist)
    f.run()
