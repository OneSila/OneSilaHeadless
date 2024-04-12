from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core import models
from django.utils.translation import gettext_lazy as _
from contacts.models import Supplier, ShippingAddress, InvoiceAddress
from products.models import Product


class SupplierProduct(models.Model):
    """
    A product can have mulitple suppliers. Let's look at that from here.
    """
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    unit = models.ForeignKey('units.Unit', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey('contacts.Company', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product} <{self.supplier}>"

    def save(self, *args, **kwargs):
        if not self.product.is_variation():
            raise IntegrityError(_("Inventory can only be attached to a VARIATION. Not a {}".format(self.product.type)))

        super().save(*args, **kwargs)

    class Meta:
        search_terms = ['sku', 'name', 'supplier__name']


class PurchaseOrder(models.Model):
    """
    Buying your items is crucial of course.
    """
    DRAFT = 'DRAFT'
    ORDERED = 'ORDERED'
    CONFIRMED = 'CONFIRMED'
    PENDING_DELIVERY = 'PENDING_DELIVERY'
    DELIVERED = 'DELIVERED'

    PO_STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (ORDERED, _("Ordered")),
        (CONFIRMED, _("Confirmation Received")),
        (PENDING_DELIVERY, _("Pending Delivery")),
        (DELIVERED, _("Delivered")),
    )

    status = models.CharField(max_length=16, choices=PO_STATUS_CHOICES)
    supplier = models.ForeignKey('contacts.Company', on_delete=models.PROTECT)
    order_reference = models.CharField(max_length=100)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)

    invoice_address = models.ForeignKey(InvoiceAddress, on_delete=models.PROTECT, related_name="invoice_address_set")
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, related_name="shipping_address_set")

    @property
    def total_value(self):
        from django.db.models import Sum, F

        total = self.purchaseorderitem_set.aggregate(
            total_sum=Sum(F('quantity') * F('unit_price'))
        )['total_sum']

        if total is None:
            return f"0 {self.currency.symbol}"

        # Return the total sum with the currency symbol
        return f"{total} {self.currency.symbol}"

    def reference(self):
        return f"PO{self.id}"

    def __str__(self):
        return self.reference()

    class Meta:
        search_terms = ['supplier__name', 'order_reference']


class PurchaseOrderItem(models.Model):
    """
    Items being purchased from through a given purchase order
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    item = models.ForeignKey(SupplierProduct, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.FloatField()

    class Meta:
        search_terms = ['purchase_order__order_reference', 'purchase_order__supplier__name']
        unique_together = ("purchase_order", "item")
