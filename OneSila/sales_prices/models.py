from core import models
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from .managers import SalesPriceManager, SalesPriceListItemManager, SalesPriceListManager


class SalesPrice(models.Model):
    '''
    Once a price for a product is created, the 'children' will be created and updated automaically.

    Meaning, if price in EUR is created, all child currency prices like GBP, CHF,
    all will get a new price.

    Or if the EUR prices changes, the rest is adjusted based on the known currencies.

    But also if the rate changes on ex CHF, the children will receive an update.
    '''
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.CASCADE)

    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    discount_amount = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)

    objects = SalesPriceManager()

    def __str__(self):
        return '{} {}'.format(self.amount, self.currency)

    @property
    def tax_rate(self):
        return self.product.taxassign.tax.rate

    @property
    def amount_ex_vat(self):
        '''
        Prices are incl VAT.  Calculate and return the net amount.
        '''
        return self.amount - (self.amount / self.tax_rate)

    @property
    def parent_aware_amount(self):
        '''
        If the currency has a parent, then one needs this price to calculate
        the new price
        '''
        try:
            sales_price = self.currency.inherits_from.salesprice_set.get(product=self.product)
            return sales_price.amount
        except AttributeError:  # happens when iherits_from is null
            return self.amount

    @property
    def parent_aware_discount_amount(self):
        '''
        If the currency has a parent, then one needs this price to calculate
        the new discount_amount
        '''
        try:
            sales_price = self.currency.inherits_from.salesprice_set.get(product=self.product)
            return sales_price.discount_amount
        except AttributeError:  # happens when iherits_from is null, or in other words you are the parent.
            return self.discount_amount

    class Meta:
        unique_together = ('product', 'currency')


class SalesPriceList(models.Model):
    """
    The Sales Price Lists are used to assign bespoke prices to specific customers.
    For example retail-customers or wholesale customers.

    They can either be auto-updating based on a discount. Or you can manually set prices.

    Items are not to be automatically added. This should be a manual process.
    """
    name = models.CharField(max_length=100)
    discount = models.FloatField(null=True, blank=True)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    vat_included = models.BooleanField(default=False)
    auto_update = models.BooleanField(default=True)  # Unclear what this means
    # include_all_products = models.BooleanField(default=False) # new line

    start_date = models.DateField(_("start date"), blank=True, null=True)
    end_date = models.DateField(_("end date"), blank=True, null=True)

    customers = models.ManyToManyField('contacts.Company', blank=True)

    objects = SalesPriceListManager()

    def __str__(self):
        return '{} {}'.format(self.name, self.currency)

    class Meta:
        search_terms = ['name']


class SalesPriceListItem(models.Model):
    salespricelist = models.ForeignKey(SalesPriceList, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    salesprice = models.FloatField(blank=True, null=True)

    objects = SalesPriceListItemManager()

    def __str__(self):
        return '{} {}'.format(self.product, self.salespricelist)

    def set_new_salesprice(self, new_price):
        self.salesprice = new_price
        self.save()

    @property
    def retail_price(self):
        '''return the currency aware retail price'''
        return self.product.salesprice_set.get_currency_price(
            self.salespricelist.currency.iso_code)

    class Meta:
        unique_together = ('product', 'salespricelist')
