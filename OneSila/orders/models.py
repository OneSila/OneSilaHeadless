from core import models
from currency_converter import CurrencyConverter, RateNotFoundError

from .managers import OrderItemManager, OrderManager


class Order(models.SetStatusMixin, models.Model):
    reference = models.CharField(max_length=100, blank=True, null=True)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    price_incl_vat = models.BooleanField(default=True)
    source = models.ForeignKey('integrations.Integration', on_delete=models.PROTECT, null=True, blank=True)  # we can have manual orders

    objects = OrderManager()

    @property
    def total_value(self):
        ''' return the total value in its original currency'''
        return self.orderitem_set.total_value() or 0.0

    @property
    def total_value_gbp(self):
        return self.total_value_custom_currency('GBP')

    @property
    def total_value_currency(self):
        total_value = self.total_value

        if total_value:
            return '{} {}'.format(self.currency.symbol, total_value)
        else:
            return total_value

    def __str__(self):
        return '#{}'.format(self.id)

    def total_value_custom_currency(self, currency_symbol):
        '''return the total_value in the given currency'''
        if self.currency.iso_code != currency_symbol:  # FIXME: Detect default currency instead
            c = CurrencyConverter()
            try:
                return c.convert(self.total_value, self.currency.iso_code, currency_symbol, date=self.created_at)
            except RateNotFoundError:
                return c.convert(self.total_value, self.currency.iso_code, currency_symbol)
        else:
            return self.total_value

    class Meta:
        ordering = ('-created_at',)
        search_terms = ['reference', 'customer__name']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # Price can be blank as we'll do auto-pricing in certain cases.
    price = models.FloatField(blank=True, null=True)

    objects = OrderItemManager()

    def __str__(self):
        return '{} x {} : {}'.format(self.product.sku, self.quantity, self.order)

    @property
    def subtotal(self):
        return round(self.quantity * self.price, 2)

    def subtotal_string(self):
        currency_symbol = self.order.currency.symbol
        subtotal = self.subtotal
        return f"{currency_symbol} {subtotal}"

    @property
    def value_gbp(self):
        return self.value_custom_currency('GBP')

    def value_custom_currency(self, currency_symbol):
        '''return the total_value in the given currency'''
        price = self.price

        if self.order.currency.iso_code != currency_symbol:  # FIXME: Detect default currency instead
            c = CurrencyConverter()
            try:
                price = c.convert(self.price, self.order.currency.iso_code, currency_symbol, date=self.order.created_at)
            except RateNotFoundError:
                price = c.convert(self.price, self.order.currency.iso_code, currency_symbol)

        return price * self.quantity

    class Meta:
        search_terms = ['order__reference', 'order__company__name']
        unique_together = ("order", "product")


class OrderNote(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    note = models.TextField()

    def __str__(self):
        return '{}'.format(self.order)

    class Meta:
        search_terms = ['order__reference', 'order__company__name', 'note']
