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


class SalesPriceListItemGeneratorUpdater:
    def __init__(self, pricelist, product):
        self.pricelist = pricelist
        self.currency_iso = pricelist.currency.iso_code
        self.discount = pricelist.discount
        self.product = product

    def _create_item(self):
        old_price = self.product.salesprice_set.get_currency_price(self.currency_iso).amount
        new_price = old_price - old_price * (self.discount / 100)

        try:
            self.item = self.pricelist.salespricelistitem_set.get(
                product=self.product)
            self.item.set_new_salesprice(new_price)
            self.item_created = False
        except SalesPriceListItem.DoesNotExist:
            self.item = self.pricelist.salespricelistitem_set.create(
                product=self.product,
                salesprice=new_price)
            self.item_created = True

    def run(self):
        self._create_item()


class SalesPriceListItemBulkGeneratorUpdater:
    def __init__(self, pricelist, products):
        self.pricelist = pricelist
        self.products = products

    def _create_items(self, product):
        fac = SalesPriceListItemGeneratorUpdater(self.pricelist, product)
        fac.run()

    def run(self):
        [self._create_items(p) for p in self.products]


class SalesPriceGenerator:
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
