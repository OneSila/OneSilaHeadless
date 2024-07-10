from core import models
from customs.managers import HsCodeManager
from products.models import Product


class HsCode(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=12)

    # @TODO: This sohuld probably be called "products"
    product = models.ManyToManyField(Product, blank=True)
    objects = HsCodeManager()

    def __str__(self):
        return f"{self.name} <{self.code}>"

    class Meta:
        search_terms = ['name', 'code']
