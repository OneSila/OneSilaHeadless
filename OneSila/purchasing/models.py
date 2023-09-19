from core import models
from django.db import models
from django.utils.translation import gettext_lazy as _
from contacts.models import Supplier, InternalCompany, ShippingAddress
from products.models import ProductVariation


class SupplierProduct(models.Model):
    """
    A product can have mulitple suppliers. Let's look at that from here.
    """
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)
    unit = models.ForeignKey('units.Unit', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    product = models.ForeignKey(ProductVariation, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product} <{self.supplier}>"


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

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_reference = models.CharField(max_length=100)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT)

    invoice_address = models.ForeignKey(InternalCompany, on_delete=models.PROTECT)
    delivery_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT)

    def reference(self):
        return f"PO{self.id}"

    def __str__(self):
        return self.reference()


class PurchaseOrderItem(models.Model):
    """
    Items being purchased from through a given purchase order
    """
    item = models.ForeignKey(SupplierProduct, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.FloatField()
