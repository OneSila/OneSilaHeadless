from currencies.models import Currency
from eancodes.models import EanCode
from sales_prices.models import SalesPriceList, SalesPriceListItem, SalesPrice

from io import BytesIO
from datetime import datetime
from xlsxwriter.workbook import Workbook


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
