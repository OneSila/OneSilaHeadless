from django.db import models
from django.db.models import Sum

from orders.models import Order

import logging
logger = logging.getLogger(__name__)


# https://simpleisbetterthancomplex.com/tips/2016/08/16/django-tip-11-custom-manager-with-chainable-querysets.html
# Use Queryset before manager to make everythin chainable


class ProductStockQuerySet(models.QuerySet):
    def available(self):
        '''
        if one of the locations is marked as quantity -1 - force stock
        '''
        return self.physical() - self. sold()

    def sold(self):
        sold_stock = self._hints['instance'].orderitem_set.all().exclude(
            order__status__in=Order.DONE_TYPES).aggregate(Sum('quantity'))['quantity__sum'] or 0

        return sold_stock

    def physical(self):
        stock = self.all().aggregate(Sum('quantity'))['quantity__sum'] or 0

        if self.filter(quantity=-1) or not self._hints['instance'].is_shippable:
            stock = 999

        return stock

    def saleable(self):
        available = self.available()

        if available >= 0:
            return available
        else:
            return 0

    def set_unlimited_stock(self, product):
        from .models import StockLocation
        location, _ = StockLocation.objects.get_or_create(name='DUMMY')

        stock, _ = self.model.objects.get_or_create(location=location, product=product)
        stock.quantity = -1
        stock.save()

    def unset_unlimited_stock(self, product):
        from .models import StockLocation
        location, _ = StockLocation.objects.get_or_create(name='DUMMY')

        try:
            stock = self.model.objects.get(location=location, product=product)
            stock.delete()
        except self.model.DoesNotExist:
            logger.debug('Failed to find stock')


class ProductStockManager(models.Manager):
    def get_queryset(self):
        return ProductStockQuerySet(self.model, using=self._db)  # Important!

    def available(self):
        return self.get_queryset().available()

    def sold(self):
        return self.get_queryset().sold()

    def physical(self):
        return self.get_queryset().physical()

    def saleable(self):
        return self.get_queryset().saleable()

    def set_unlimited_stock(self):
        return self.get_queryset().set_unlimited_stock(self.instance)

    def unset_unlimited_stock(self):
        return self.get_queryset().unset_unlimited_stock(self.instance)
