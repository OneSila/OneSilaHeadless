from core import models
from products.models import Product


class HsCode(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=12)
    product = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"{self.name} <{self.code}>"

    class Meta:
        search_terms = ['name', 'code']
