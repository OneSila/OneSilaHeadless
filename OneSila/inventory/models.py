from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core import models
from .managers import InventoryManager, InventoryLocationManager


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
