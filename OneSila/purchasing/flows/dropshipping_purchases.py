from purchasing.factories import BuyDropShippingProductsFactory


def buy_dropshippingproducts_flow(order):
    f = BuyDropShippingProductsFactory(order)
    f.run()
