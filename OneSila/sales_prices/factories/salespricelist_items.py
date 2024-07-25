from decimal import Decimal
from currencies.models import Currency
from currencies.helpers import roundup
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


When a SalesPrice is updated
- update the relevant salespricelist-item price when the lists are set to auto-price updates

When a currency rate is updated:
- update the relevant prices where the price-list is set to auto-price updates

"""


class SalesPriceItemAutoPriceUpdateMixin:
    def run_update_cycle(self):
        for spi in self.salespricelistitems.iterator():
            self.update_salespricelistitem(spi)

    @staticmethod
    def calculate_price(from_price, conversion_factor, round_prices_up_to, is_discount=True):
        if conversion_factor == 0:
            raise ValueError("Conversion Factor cannot be 0. Did you mean None?")

        if conversion_factor is None:
            return from_price

        from_price = Decimal(from_price)
        conversion_factor = Decimal(conversion_factor)

        price_diff = from_price / (conversion_factor / 100)

        if conversion_factor < 0 or conversion_factor > 1:
            conversion_factor = conversion_factor / 100

        price_diff = from_price * conversion_factor

        if is_discount:
            to_price = from_price - price_diff
        else:
            to_price = from_price + price_diff

        return roundup(to_price, round_prices_up_to)

    def get_salesprice(self, salespricelistitem):
        return salespricelistitem.product.salesprice_set.get(
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company)

    def update_salespricelistitem(self, salespricelistitem):
        # Two fields need updating:
        # - price_auto
        # - discount_auto
        # and they need to respect the rounding on the currency

        # We calculate the new price and discount based on the highest price received from the SalesPrice
        sales_price = self.get_salesprice(salespricelistitem)
        highest_price = sales_price.highest_price()

        conversion_factor = salespricelistitem.salespricelist.price_change_pcnt
        salespricelistitem.price = self.calculate_price(highest_price,
            conversion_factor=conversion_factor,
            round_prices_up_to=self.currency.round_prices_up_to,
            is_discount=False)

        conversion_factor = salespricelistitem.salespricelist.discount_pcnt
        salespricelistitem.discount = self.calculate_price(highest_price,
            conversion_factor=conversion_factor,
            round_prices_up_to=self.currency.round_prices_up_to,
            is_discount=True)

        salespricelistitem.save()


class SalesPriceListForSalesPriceListItemUpdatePricesFactory(SalesPriceItemAutoPriceUpdateMixin):
    """
    When a salesprice is adjusted, we need to revisit all attached
    salespricelistitem items if auto-price-update is switched on.
    """

    def __init__(self, salespricelist):
        self.salespricelist = salespricelist
        self.currency = salespricelist.currency
        self.multi_tenant_company = salespricelist.multi_tenant_company

    def preflight_approval(self):
        return self.salespricelist.auto_update_prices

    def set_salespricelistitems(self):
        self.salespricelistitems = self.salespricelist.salespricelistitem_set.all()

    def run(self):
        if self.preflight_approval():
            self.set_salespricelistitems()
            self.run_update_cycle()


class SalesPriceForSalesPriceListItemUpdatePricesFactory(SalesPriceItemAutoPriceUpdateMixin):
    """
    When a sales-prices changes, we want to update all relevant SalesPriceListItems
    when marked as auto-update-prices
    """

    def __init__(self, sales_price):
        self.sales_price = sales_price
        self.product = sales_price.product
        self.currency = sales_price.currency
        self.multi_tenant_company = sales_price.multi_tenant_company

    def set_salespricelists(self):
        self.salespricelists = SalesPriceList.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            auto_update_prices=True,
            currency=self.currency)

    def set_salespricelistitems(self):
        self.salespricelistitems = SalesPriceListItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            salespricelist__in=self.salespricelists
        )

    def run(self):
        self.set_salespricelists()
        self.set_salespricelistitems()
        self.run_update_cycle()


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
