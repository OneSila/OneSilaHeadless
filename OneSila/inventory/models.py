from core import models
from .managers import InventorykManager


class Inventory(models.Model):
    '''
    Class to store quantity of products on stock
    '''
    product = models.ForeignKey('products.ProductVariation', on_delete=models.PROTECT,
        related_name='stock')
    stocklocation = models.ForeignKey('InventoryLocation', on_delete=models.PROTECT)
    quantity = models.IntegerField()

    objects = InventorykManager()

    class Meta:
        unique_together = ('product', 'stocklocation')

    def __str__(self):
        return '{}: {}@{}'.format(self.product, self.stocklocation, self.quantity)

    def save(self, *args, **kwargs):
        if not self.product.is_variation():
            raise IntegrityError(_("Inventory can only be attached to a VARIATION. Not a {}".format(self.product.type)))


class InventoryLocation(models.Model):
    '''
    Class to keep track of stock-locations.   These can be used in many was:
    - Physical location / address or warehouse
    - Location inside of location: Shelf 1, Rack B, Col 3
    Just remember to chain the locatons.
    '''
    name = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    parent_location = models.ForeignKey('self', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
