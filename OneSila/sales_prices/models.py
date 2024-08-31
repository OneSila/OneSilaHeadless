from core import models
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from .managers import SalesPriceManager, SalesPriceListItemManager, SalesPriceListManager
from decimal import Decimal


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

    rrp = models.DecimalField(_("Reccomended Retail Price"), decimal_places=2, max_digits=10,
        null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=10,
        null=True, blank=True)

    objects = SalesPriceManager()

    class Meta:
        unique_together = ('product', 'currency', 'multi_tenant_company')
        constraints = [
            models.CheckConstraint(
                check=models.Q(rrp__gte=models.F("price")),
                name=_("RRP cannot be less then the price"),
            ),
            models.CheckConstraint(
                check=models.Q(rrp__gte='0.01'),
                name=_("RRP cannot be 0"),
            ),
            models.CheckConstraint(
                check=models.Q(price__gte='0.01'),
                name=_("Price cannot be 0"),
            ),
        ]

    def get_real_price(self):
        """Which is applicable?  RRP or Price?"""
        prices = []

        if self.rrp:
            prices.append(self.rrp)

        if self.price:
            prices.append(self.price)

        return min(prices)

    def __str__(self):
        return '{} {}'.format(self.rrp, self.currency)

    def clean(self):
        super().clean()

        if self.rrp is None and self.price is None:
            raise ValidationError(_("You need to supply either RRP or Price."))

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
        except self.DoesNotExist:
            return None

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
        except self.DoesNotExist:
            return None

    def highest_price(self):
        return max([self.rrp or 0, self.price or 0])

    def set_prices(self, *, rrp, price):
        self.rrp = rrp
        self.price = price
        self.save()


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
    # Answer: The order should be set the the detected pricelist currency
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    vat_included = models.BooleanField(_("Price list includes VAT"),
        default=False)
    auto_update_prices = models.BooleanField(_("Auto Update Price and Discount Price"),
        default=True)
    auto_add_products = models.BooleanField(_("Auto add all products"),
        default=False)
    price_change_pcnt = models.FloatField(null=True, blank=True,
        help_text=_("How would you like to influence the max price?  Write 20 to increase it with 20%.  Or -20 to decrease with 20\%"))
    discount_pcnt = models.FloatField(null=True, blank=True,
        help_text=_("What percentage discount would you like to apply?  For a 20\% discount, write 20"))
    notes = models.TextField(blank=True, null=True)

    objects = SalesPriceListManager()

    def __str__(self):
        return '{} {}'.format(self.name, self.currency)

    class Meta:
        search_terms = ['name']
        ordering = ['-id']


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

    class Meta:
        unique_together = ('product', 'salespricelist', 'multi_tenant_company')
        base_manager_name = 'objects'
