from currencies.models import Currency
from sales_prices.models import SalesPriceList, SalesPriceListItem, SalesPrice

"""
Possible scenarios:
- B2B client with specific price = manual price update + manual product assign
- B2C list for BFCM = massive discounts on some products = manual product assign + possible auto-price updates + time restriction
- B2B list for all customers with fixed discount in another geographical region = auto-price + auto-assign



A few jobs need doing
When a price list is created or updated
- eg discount changed
- auto flag is changed
- date range is changed or empty (dont update if in the past)
- related currency rate is changed
1. Create SalesPriceListItems if the thing is auto-populate.
2. Update the prices when currency rates change
Missing field? include_all_products
rename field? discount_amount to discount_percentage
rename Field? auto_update to auto_update_prices? and make discount_percentage dependent on this one?

When a SalesPrice is Created
- Create the relevant salespricelist-items when the lists are set to auto-product add mode.

When a SalesPrice is updated
- update the relevant salespricelist-item price when the lists are set to auto-price updates

When a currency rate is updated:
- update the relevant prices where the price-list is set to auto-price updates


Sales Price adjustment
- price -> RRP (Reccomended Retail Price)
- discount -> Price

And then our price lists can be used for discounts.
And we restrict overusage of price lists.
"""

# old code:


# SalesPriceList:
# - signal auto_add_products field changed
# - signal salesprice created
# - auto_add_products = Grab and use all of the salesprice items that use the relevan currency

# What to do?
# - factory to create the relevant items
# - factory to update prices on the relevant items when auto_update_prices (also for the created ones)


class SalesPriceForSalesPriceListItemCreateFactory:
    """
    When a sales-price is created, we want to
    create all relevant SalesPriceListItems immediatly
    """

    def __init__(self, sales_price):
        self.sales_price = sales_price
        self.product = sales_price.product
        self.currency = sales_price.currency
        self.multi_tenant_company = sales_price.multi_tenant_company

    def set_salespricelists(self):
        self.salespricelists = SalesPriceList.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency,
            auto_add_products=True)

    def create_salespricelistpriceitems(self):
        for price_list in self.salespricelists:
            price_list.salespricelistitem_set.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product
            )

    def run(self):
        self.set_salespricelists()
        self.create_salespricelistpriceitems()


class SalesPriceListForSalesPriceListItemsCreateUpdateFactory:
    """
    When a salespricelist is created, we want to create
    all relevant salespricelistitems
    """

    def __init__(self, *, salespricelist):
        self.salespricelist = salespricelist
        self.currency = salespricelist.currency
        self.multi_tenant_company = salespricelist.multi_tenant_company

    def preflight_approval(self):
        return self.salespricelist.auto_add_products

    def set_salesprices(self):
        self.salesprices = SalesPrice.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency,
        )

    def create_salespricelistpriceitems(self):
        for salesprice in self.salesprices:
            product = salesprice.product
            self.salespricelist.salespricelistitem_set.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=product,
            )

    def run(self):
        if self.preflight_approval():
            self.set_salesprices()
            self.create_salespricelistpriceitems()


# class SalesPriceListItemGeneratorUpdater:
#     def __init__(self, pricelist, product):
#         self.pricelist = pricelist
#         self.currency_iso = pricelist.currency.iso_code
#         self.discount = pricelist.discount
#         self.product = product

#     def _create_item(self):
#         old_price = self.product.salesprice_set.get_currency_price(self.currency_iso).amount
#         new_price = old_price - old_price * (self.discount / 100)

#         try:
#             self.item = self.pricelist.salespricelistitem_set.get(
#                 product=self.product)
#             self.item.set_new_salesprice(new_price)
#             self.item_created = False
#         except SalesPriceListItem.DoesNotExist:
#             self.item = self.pricelist.salespricelistitem_set.create(
#                 product=self.product,
#                 salesprice=new_price)
#             self.item_created = True

#     def run(self):
#         self._create_item()


class SalesPriceGenerator:
    """
    this generator is used to generate demo-data.
    """

    def __init__(self, name, discount, currency_iso, product_list):
        self.currency = Currency.objects.get(iso_code=currency_iso)
        self.name = name
        self.discount = discount
        self.product_list = product_list

    def _create_pricelist(self):
        self.salespricelist = SalesPriceList.objects.create(
            name=self.name,
            currency=self.currency,
            discount=self.discount)

    def _destroy_pricelist(self):
        self.salespricelist.delete()

    def _create_pricelistitem(self, product):
        try:
            ori_price = product.salesprice_set.get_currency_price(self.currency.iso_code).amount
            new_price = ori_price - ori_price * (self.discount / 100)

            SalesPriceListItem.objects.create(
                salespricelist=self.salespricelist,
                product=product,
                salesprice=new_price)
        except Exception as e:
            raise Exception('Failed to create item for product {}'.format(product)).with_traceback(e.__traceback__)

    def _run_pricelistitems(self):
        for prod in self.product_list:
            self._create_pricelistitem(prod)

    def run(self):
        self._create_pricelist()

        try:
            self._run_pricelistitems()
        except Exception as e:
            self._destroy_pricelist()
            raise
