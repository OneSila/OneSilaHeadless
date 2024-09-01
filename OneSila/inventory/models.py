from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core import models
from .managers import InventoryManager, InventoryLocationManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from purchasing.models import PurchaseOrder
# FIXME: Add once returns are merged into the main branch.
# from order_returns import OrderReturn
from orders.models import Order
from shipments.models import Package

from .signals import inventory_received, inventory_sent


class Inventory(models.Model):
    '''
    Class to store quantity of products on stock
    '''
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT,
        related_name='inventory')
    inventorylocation = models.ForeignKey('InventoryLocation', on_delete=models.PROTECT)
    quantity = models.IntegerField()

    objects = InventoryManager()

    class Meta:
        backorder_item_count = 99999
        search_terms = ['product__sku', 'inventorylocation__name', 'product__supplier__name']
        unique_together = ('product', 'inventorylocation')
        verbose_name_plural = "inventories"

    def reduce_quantity(self, quantity):
        self.quantity -= quantity
        self.save()

    def increase_quantity(self, quantity):
        self.quantity += quantity
        self.save()

    def __str__(self):
        return '{}: {}@{}'.format(self.product, self.inventorylocation, self.quantity)

    def save(self, *args, **kwargs):
        if not (self.product.is_supplier_product() or self.product.is_manufacturable()):
            raise IntegrityError(_("Inventory can only be attached to a SUPPLIER or MANUFACTURABLE PRODUCT. Not a {}".format(self.product.type)))

        super().save(*args, **kwargs)


class InventoryLocation(models.Model):
    '''
    Class to keep track of stock-locations.   These can be used in many was:
    - Physical location / address or warehouse
    - Location inside of location: Shelf 1, Rack B, Col 3
    Just remember to chain the locatons.
    '''
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    shippingaddress = models.ForeignKey('contacts.InventoryShippingAddress', on_delete=models.CASCADE)

    precise = models.BooleanField(default=False)

    objects = InventoryLocationManager()

    def __str__(self):
        return self.name

    # @property
    # def is_internal_location(self):
    #     return self.shippingaddress.company.is_internal_company

    class Meta:
        search_terms = ['name']
        unique_together = ("name", "multi_tenant_company")


class InventoryMovement(models.Model):
    """
    Represents an inventory movement record, capable of dynamically referencing different types of sources and destinations.
    """
    MOVEMENT_FROM_MODELS = [
        PurchaseOrder,
        Inventory,
        # FIXME: Add once returns are merged into the main branch.
        # OrderReturn
    ]
    MOVEMENT_TO_MODELS = [Inventory, Package]

    # Source of inventory movement (e.g., from a warehouse, a purchase order or return)
    mf_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='inventory_movements_from')
    mf_object_id = models.PositiveIntegerField()
    movement_from = GenericForeignKey("mf_content_type", "mf_object_id")

    # Destination of inventory movement (e.g., to a sales order, another warehouse)
    mt_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='inventory_movements_to')
    mt_object_id = models.PositiveIntegerField()
    movement_to = GenericForeignKey("mt_content_type", "mt_object_id")

    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} from {self.movement_from} to {self.movement_to}"

    def save(self, *args, **kwargs):
        if self.movement_from == self.movement_to:
            raise IntegrityError(f"You cannot move from and to the same location. Ensure movement_to is different from movement_from.")

        mf_class = self.mf_content_type.model_class()
        if not mf_class in self.MOVEMENT_FROM_MODELS:
            raise IntegrityError(f"You can only receive inventory from {self.MOVEMENT_FROM_MODELS}, not {mf_class}")

        mt_class = self.mt_content_type.model_class()
        if not mt_class in self.MOVEMENT_TO_MODELS:
            raise IntegrityError(f"You can only receive inventory from {self.MOVEMENT_TO_MODELS} not {mt_class}")

        super().save(*args, **kwargs)

        # Share the update through OneSila so other apps can
        # take action where needed.
        inventory_received.send(
            sender=self.movement_to.__class__,
            instance=self.movement_to,
            product=self.product,
            quantity_received=self.quantity,
            movement_from=self.movement_from)
        inventory_sent.send(
            sender=self.movement_from.__class__,
            instance=self.movement_from,
            product=self.product,
            quantity_sent=self.quantity,
            movement_to=self.movement_to)

    class Meta:
        indexes = [
            models.Index(fields=['mf_content_type', 'mf_object_id']),
            models.Index(fields=['mt_content_type', 'mt_object_id']),
            models.Index(fields=['mf_content_type', 'mf_object_id', 'mt_content_type', 'mt_object_id']),
        ]
        # ordering = ['-created_at']  # Default ordering by creation date, descending
