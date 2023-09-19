from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin

from .managers import ProductStockManager


class ProductStock(MultiTenantAwareMixin, models.Model):
    '''
    Class to store quantity of proudcts
    '''
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT,
        related_name='stock')
    location = models.ForeignKey('StockLocation', on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0,
        verbose_name='Quantity (-1 to force availabilty)')  # -1 == always on stock.

    objects = ProductStockManager()

    class Meta:
        unique_together = ('product', 'location')

    def __str__(self):
        return '{}: {}@{}'.format(self.product, self.location, self.quantity)

    def save(self, *args, **kwargs):
        if not self.product.is_variation():
            raise IntegrityError(_("Inventory can only be attached to a VARIATION. Not a {}".format(self.product.type)))


class Warehouse(MultiTenantAwareMixin, models.Model):
    name = models.CharField(max_length=100)


class StockLocation(MultiTenantAwareMixin, models.Model):
    '''
    Class to keep track of stock-locations.   These can be used in many was:
    - Physical location / address or warehouse
    - Location inside of location: Shelf 1, Rack B, Col 3
    '''
    name = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class MinimumStock(MultiTenantAwareMixin, models.Model):
    '''
    Class to set an expected minimum-stock for a given product.
    '''
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE)
    num_required = models.IntegerField(default=0)

    def __str__(self):
        return '{}x {}'.format(self.num_required, self.product)

    def save(self, *args, **kwargs):
        if self.product.is_umbrella():
            raise IntegrityError(_("You can only assign a minimum-stock to a VARIATION or BUNDLE"))
