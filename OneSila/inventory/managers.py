from core import models
from core.models import Sum

from orders.models import Order

import logging
logger = logging.getLogger(__name__)


class InventoryQuerySet(models.QuerySet):
    def salable(self):
        """Items that are available for sale"""
        if self._hints['instance'].product.always_on_stock:
            return 999

        return self.physical() - self.reserved()

    def physical(self):
        """physically on stock, could be reserved, could be salable"""
        physical_agg = self.\
            all().\
            aggregate(Sum('quantity'))

        return physical_agg['quantity__sum'] or 0

    def reserved(self):
        """Items that have been sold but not shipped"""
        sold_agg = self._hints['instance'].orderitem_set.\
            all().\
            exclude(
                order__status__in=Order.DONE_TYPES).\
            aggregate(Sum('quantity'))

        return sold_agg['quantity__sum'] or 0


class InventorykManager(models.Manager):
    def get_queryset(self):
        return InventoryQuerySet(self.model, using=self._db)

    def salable(self):
        return self.get_queryset().salable()

    def physical(self):
        return self.get_queryset().physical()

    def reserved(self):
        return self.get_queryset().reserved()
