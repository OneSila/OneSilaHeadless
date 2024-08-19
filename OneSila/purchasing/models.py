from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core import models
from django.utils.translation import gettext_lazy as _
from contacts.models import ShippingAddress, InvoiceAddress
from products.models import SupplierProduct


class PurchaseOrder(models.Model):
    """
    Buying your items is crucial of course.
    """
    DRAFT = 'DRAFT'
    TO_ORDER = 'TO_ORDER'
    ORDERED = 'ORDERED'
    CONFIRMED = 'CONFIRMED'
    PENDING_DELIVERY = 'PENDING_DELIVERY'
    DELIVERED = 'DELIVERED'

    PO_STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (TO_ORDER, _("To Order")),
        (ORDERED, _("Ordered")),
        (CONFIRMED, _("Confirmation Received")),
        (PENDING_DELIVERY, _("Pending Delivery")),
        (DELIVERED, _("Delivered")),
    )

    status = models.CharField(max_length=16, choices=PO_STATUS_CHOICES)
    supplier = models.ForeignKey('contacts.Company', on_delete=models.PROTECT)
    order_reference = models.CharField(max_length=100, blank=True, null=True)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    order = models.ForeignKey('orders.Order', blank=True, null=True, on_delete=models.PROTECT)

    invoice_address = models.ForeignKey(InvoiceAddress, on_delete=models.PROTECT, related_name="invoice_address_set")
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, related_name="shipping_address_set")

    def is_draft(self):
        return self.status == self.DRAFT

    def is_to_order(self):
        return self.status == self.TO_ORDER

    def is_ordered(self):
        return self.status == self.ORDERED

    def is_confirmed(self):
        return self.status == self.CONFIRMED

    def is_pending_delivery(self):
        return self.status == self.PENDING_DELIVERY

    def is_delivered(self):
        return self.status == self.DELIVERED

    def set_status(self, status):
        self.status = status
        self.save()

    def set_status_draft(self):
        self.set_status(self.DRAFT)

    def set_status_to_order(self):
        self.set_status(self.TO_ORDER)

    def set_status_ordered(self):
        self.set_status(self.ORDERED)

    def set_status_confirmed(self):
        self.set_status(self.CONFIRMED)

    def set_status_pending_delivey(self):
        self.set_status(self.PENDING_DELIVERY)

    def set_status_delivered(self):
        self.set_status(self.DELIVERED)

    @property
    def total_value(self):
        from django.db.models import Sum, F

        sum = self.purchaseorderitem_set.aggregate(
            total_sum=Sum(F('quantity') * F('unit_price'))
        )['total_sum']

        if sum is None:
            return f"0 {self.currency.symbol}"

        total = round(sum, 2)

        if total is None:
            return f"0 {self.currency.symbol}"

        # Return the total sum with the currency symbol
        return f"{total} {self.currency.symbol}"

    def reference(self):
        return f"PO{self.id}"

    def __str__(self):
        return self.order_reference or self.reference()

    def save(self, *args, **kwargs):

        # if we buy from someone it mean it become a customer if is not already
        if not self.supplier.is_supplier:
            self.supplier.is_supplier = True
            self.supplier.save()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-created_at',)
        search_terms = ['supplier__name', 'reference']


class PurchaseOrderItem(models.Model):
    """
    Items being purchased from through a given purchase order
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(SupplierProduct, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    orderitem = models.ForeignKey('orders.OrderItem', null=True, blank=True,
        on_delete=models.CASCADE)

    class Meta:
        search_terms = ['purchase_order__reference', 'purchase_order__supplier__name']
        unique_together = ("purchase_order", "product")
