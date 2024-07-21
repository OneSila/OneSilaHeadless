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

    rrp = models.DecimalField(_("Reccomended Retail Price"),
        default=0.0, decimal_places=2, max_digits=10)
    price = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)

    objects = SalesPriceManager()

    def __str__(self):
        return '{} {}'.format(self.rrp, self.currency)

    @property
    def tax_rate(self):
        return self.product.taxassign.tax.rate

    @property
    def rrp_ex_vat(self):
        '''
        Prices are incl VAT.  Calculate and return the net amount.
        '''
        return self.rrp - (self.rrp / self.tax_rate)

    @property
    def parent_aware_rrp(self):
        '''
        If the currency has a parent, then one needs this price to calculate
        the new price
        '''
        try:
            sales_price = self.currency.inherits_from.salesprice_set.get(product=self.product)
            return sales_price.rrp
        except AttributeError:  # happens when iherits_from is null
            return self.rrp

    @property
    def parent_aware_price(self):
        '''
        If the currency has a parent, then one needs this price to calculate
        the new price
        '''
        try:
            sales_price = self.currency.inherits_from.salesprice_set.get(product=self.product)
            return sales_price.price
        except AttributeError:  # happens when iherits_from is null, or in other words you are the parent.
            return self.price

    class Meta:
        unique_together = ('product', 'currency', 'multi_tenant_company')


class SalesPriceList(models.Model):
    """
    The Sales Price Lists are used to assign bespoke prices to specific customers.
    For example retail-customers or wholesale customers.

    They can either be auto-updating based on a discount. Or you can manually set prices.

    Items are not to be automatically added. This should be a manual process.
    """
    name = models.CharField(max_length=100)
    start_date = models.DateField(_("start date"), blank=True, null=True)
    end_date = models.DateField(_("end date"), blank=True, null=True)
    customers = models.ManyToManyField('contacts.Company', blank=True)

    # FIXME: What happens if the relevant pricelist doesnt match with the customer currency
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    vat_included = models.BooleanField(_("Price list includes VAT"),
        default=False)
    auto_update_prices = models.BooleanField(_("Auto Update Price and Discount Price"),
        default=True)
    auto_add_products = models.BooleanField(_("Auto add all products"),
        default=False)
    price_change_pcnt = models.FloatField(null=True, blank=True)
    discount_pcnt = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    objects = SalesPriceListManager()

    def get_discount(self):
        if self.price_list.auto_price_mode:
            return self.discount_override or self.discount_auto
        else:
            return self.discount_override

    def __str__(self):
        return '{} {}'.format(self.name, self.currency)

    class Meta:
        search_terms = ['name']


class SalesPriceListItem(models.Model):
    salespricelist = models.ForeignKey(SalesPriceList, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)

    price_auto = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    discount_auto = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    price_override = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    discount_override = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)

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
        unique_together = ('product', 'salespricelist', 'multi_tenant_company')
        base_manager_name = 'objects'
