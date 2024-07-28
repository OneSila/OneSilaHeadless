from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core import models
from .managers import InventoryManager


class Inventory(models.Model):
    '''
    Class to store quantity of products on stock
    '''
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT,
        related_name='stock')
    stocklocation = models.ForeignKey('InventoryLocation', on_delete=models.PROTECT)
    quantity = models.IntegerField()

    objects = InventoryManager()

    class Meta:
        search_terms = ['product__sku', 'stocklocation__name', 'product__supplier__name']
        unique_together = ('product', 'stocklocation')
        verbose_name_plural = "inventories"

    def __str__(self):
        return '{}: {}@{}'.format(self.product, self.stocklocation, self.quantity)

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
    name = models.CharField(max_length=10)
    description = models.TextField(null=True, blank=True)
    location = models.ForeignKey('contacts.InternalShippingAddress', on_delete=models.CASCADE, null=True)

    precise = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        search_terms = ['name']
        unique_together = ("name", "multi_tenant_company")
