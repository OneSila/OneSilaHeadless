from core import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.translation import gettext_lazy as _

from django_shared_multi_tenant.models import MultiTenantAwareMixin

from currency_converter import CurrencyConverter, RateNotFoundError

from .managers import OrderItemManager, OrderManager, OrderReportManager


class Order(models.Model):
    DRAFT = 'DRAFT'
    PENDING = 'PENDING'
    PENDING_INVENTORY = 'PENDING_INVENTORY'
    TO_PICK = 'TOPICK'
    TO_SHIP = 'TOSHIP'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'
    HOLD = 'HOLD'
    EXCHANGED = 'EXCHANGED'
    REFUNDED = 'REFUNDED'
    LOST = 'LOST'
    MERGED = 'MERGED'
    DAMAGED = 'DAMAGED'

    UNPROCESSED = [PENDING]
    DONE_TYPES = [DONE, CANCELLED, HOLD, EXCHANGED, REFUNDED, LOST, MERGED, DAMAGED]
    HELD = [HOLD, PENDING_INVENTORY]

    STATUS_CHOICES = (
        (DRAFT, _('Draft')),
        (PENDING, _('Pending')),
        (PENDING_INVENTORY, _('Pending Inventory')),
        (TO_PICK, _('To Pick')),
        (TO_SHIP, _('To Ship')),
        (DONE, _('Done')),
        (CANCELLED, _('Cancelled')),
        (HOLD, _('On Hold')),
        (EXCHANGED, _('Exchanged')),
        (REFUNDED, _('Refunded')),
        (LOST, _('Lost')),
        (MERGED, _('Merged')),
        (DAMAGED, _('Damaged')),
    )

    SALE = 'SALE'
    RETURNGOODS = 'RETURN'
    DOCUMENTS = 'DOCUMENTS'
    SAMPLE = 'SAMPLE'
    GIFT = 'GIFT'

    REASON_CHOICES = (
        (SALE, _('Sale')),
        (RETURNGOODS, _('Return goods')),
        (SAMPLE, _('Commercial Sample')),
        (GIFT, _('Gift')),
        (DOCUMENTS, _('Documents'))
    )

    reference = models.CharField(max_length=100, blank=True, null=True)
    company = models.ForeignKey('contacts.Customer', on_delete=models.PROTECT)
    invoice_address = models.ForeignKey('contacts.InvoiceAddress', on_delete=models.PROTECT,
        related_name='invoiceaddress_set')
    shipping_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.PROTECT,
        related_name='shippingaddress_set')

    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    price_incl_vat = models.BooleanField(default=True)

    status = models.CharField(max_length=17, choices=STATUS_CHOICES, default=DRAFT)
    reason_for_sale = models.CharField(max_length=10, choices=REASON_CHOICES, default=SALE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()
    reports = OrderReportManager()

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
            return '{} {}'.format(self.currency, total_value)
        else:
            return total_value

    @property
    def on_stock(self):
        if self.status not in self.DONE_TYPES:
            for i in self.orderitem_set.all():
                if i.qty_on_stock() < i.quantity:
                    return False
            return True

    @property
    def contains_custom_products(self):
        if 'custom' in ' '.join(self.orderitem_set.all().values_list('product__name', flat=True)).lower():
            return True
        else:
            return False

    def __str__(self):
        return '#{}'.format(self.id)

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

    def set_status_processing(self):
        self.status = self.PENDING
        self.save()

    def set_status_done(self):
        self.status = self.DONE
        self.save()

    def is_done(self):
        return self.status == self.DONE


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT)

    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # Price can be blank as we'll do auto-pricing in certain cases.
    price = models.FloatField(blank=True, null=True)

    objects = OrderItemManager()

    def __str__(self):
        return '{} x {} : {}'.format(self.product.name, self.quantity, self.order)

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
            return self.product.stock.physical() - older_required_quantity

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


class OrderNote(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    note = models.TextField()

    def __str__(self):
        return '{}'.format(self.order)


#
# Signals
#

@receiver(pre_save, sender=Order)
def instockorder_topick_signal(sender, instance, **kwargs):
    '''
    If the order in in stock, then mark ik as to pick
    '''
    if instance.on_stock and \
            (instance.status in Order.UNPROCESSED or instance.status in Order.IN_PRODUCTION):
        instance.status = Order.TO_PICK


@receiver(post_save, sender='inventory.ProductStock')
def inventory_change__topick_signal(sender, instance, **kwargs):
    '''
    If the inventory changes, and the product gets stock, then check if you have
    orders that have become in stock
    '''
    product = instance.product
    if product.stock.physical():
        unprocessed_orders = [i.order for i in product.orderitem_set.filter(order__status=Order.PENDING)]

        for order in unprocessed_orders:
            if order.on_stock:
                order.status = Order.TO_PICK
                order.save()