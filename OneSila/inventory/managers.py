from core import models
from core.models import Sum
from core.managers import MultiTenantQuerySet, MultiTenantManager
from orders.models import Order

import logging
logger = logging.getLogger(__name__)


"""
Here is the thing, Supplier- and Manufacturable products both
have stock directly assigned to them.

Supplier-products are always 'hidden'.  Used for sums of inventory.
But Manufacturable products are directly assinged to websites or to bundles.
Also do we calculate how much "can" be made based on the bill of materials.

ok - so let's split his up
1. Supplier product = direct stock
2. Simple Product = Sum of supplier product stock
3. DropShop product = Sum of supplier product stock, or always for sales
3. Config Product = No stock
4. Bundle Product = Sum of the simple product, dropship product, manufacturable product and bundle product stock
5. Manufacturable = Direct stock + Manufacturable stock.  (Lead times could be a challenge here)

Do we also want access to the inventory per location?
It seems we may need to eg the paperweight.ie example where he has internal and external stock.

How to we need the stock information:
- Actual number
- Lead time for this number (lowest?)

- Number per location
- Lead time per location
"""


class InventoryQuerySet(MultiTenantQuerySet):
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


class InventoryManager(MultiTenantManager):
    def get_queryset(self):
        return InventoryQuerySet(self.model, using=self._db)

    def salable(self):
        return self.get_queryset().salable()

    def physical(self):
        return self.get_queryset().physical()

    def reserved(self):
        return self.get_queryset().reserved()
