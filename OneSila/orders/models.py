from core import models
from currency_converter import CurrencyConverter, RateNotFoundError

from .managers import OrderItemManager, OrderManager
from .documents import PrintOrder


class Order(models.SetStatusMixin, models.Model):
    reference = models.CharField(max_length=100, blank=True, null=True)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    price_incl_vat = models.BooleanField(default=True)
    source = models.ForeignKey('integrations.Integration', on_delete=models.PROTECT, null=True,  blank=True) # we can have manual orders

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

    @property
    def on_stock(self):
        if self.status not in self.DONE_TYPES:
            for i in self.orderitem_set.all():
                if i.qty_on_stock() < i.quantity:
                    return False
            return True

    def __str__(self):
        return '#{}'.format(self.id)

    def print(self):
        filename = f"{self.reference or self.__str__()}.pdf"
        printer = PrintOrder(self)
        printer.generate()
        pdf = printer.pdf
        return filename, pdf

    def tax_rate(self):
        return self.invoice_address.tax_rate

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

    def set_status_pending_processing(self):
        self.set_status(self.PENDING_PROCESSING)

    def set_status_pending_shipping_approval(self):
        self.set_status(self.PENDING_SHIPPING_APPROVAL)

    def set_status_draft(self):
        self.set_status(self.DRAFT)

    def set_status_done(self):
        self.set_status(self.DONE)

    def set_status_to_ship(self):
        self.set_status(self.TO_SHIP)

    def set_status_await_inventory(self):
        self.set_status(self.AWAIT_INVENTORY)

    def set_status_shipped(self):
        self.set_status(self.SHIPPED)

    def is_draft(self):
        return self.status == self.DRAFT

    def is_pending_processing(self):
        return self.status == self.PENDING_PROCESSING

    def is_pending_shipping_approval(self):
        return self.status == self.PENDING_SHIPPING_APPROVAL

    def is_done(self):
        return self.status == self.DONE

    def is_to_ship(self):
        return self.status == self.TO_SHIP

    def is_await_inventory(self):
        return self.status == self.AWAIT_INVENTORY

    def is_shipped(self):
        return self.status == self.SHIPPED

    def is_cancelled(self):
        return self.status == self.CANCELLED

    def is_hold(self):
        return self.status == self.HOLD

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

    def qty_on_stock(self):
        # Firstly, dont bother calculating this for order-items that dont need processing
        # it's a expensive function
        if self.order.status not in Order.DONE_TYPES:
            # It can often happen that an order looks to be on stock, but if we look closer
            # and compare with older, unprocessed orders, we'll be short on stock.
            # So first deduct the required items for older orders and then check.
            older_orderitems_with_identical_items = OrderItem.objects.filter(
                order__id__lt=self.order.id,
                product=self.product).exclude(order__status__in=Order.DONE_TYPES)
            older_required_quantity = sum([i.quantity for i in older_orderitems_with_identical_items])
            return self.product.inventory.physical() - older_required_quantity

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
