from core import models
from core.models import Sum
from core.managers import MultiTenantQuerySet, MultiTenantManager
from orders.models import Order
from products.models import Product, BundleVariation
from products.product_types import HAS_INDIRECT_INVENTORY_TYPES, \
    HAS_DIRECT_INVENTORY_TYPES, BUNDLE

import logging
logger = logging.getLogger(__name__)


class InventoryQuerySet(MultiTenantQuerySet):
    def physical(self):
        """
        Physically on stock, could be reserved, could be salable.
        Configurable products return 0, as they cannot hold physical stock.
        """

        # Calculate your directly attached inventory (For manufacturable products)
        product = self._hints['instance']
        qty = 0

        if product.type in HAS_DIRECT_INVENTORY_TYPES:
            qty += self.\
                all().\
                aggregate(Sum('quantity'))['quantity__sum'] or 0

        if product.type in HAS_INDIRECT_INVENTORY_TYPES:
            supplier_product_ids = product.supplier_products.\
                all().\
                values('id')
            indirect_qs = self.model.objects.\
                filter(product_id__in=supplier_product_ids)
            qty += indirect_qs.\
                aggregate(Sum('quantity'))['quantity__sum'] or 0

        if product.type in [BUNDLE]:
            # Even though we can attach a variety of bundles, we must ensure we
            # dont sum them, but use min.  Why? Let's take an example. A bundle existing of a phone + 2 covers:
            # Phone: 100 items
            # Cover: 30
            # That means we can only ship 15x Phone+cover since the cover only has 30 pieces of which 2 are needed.
            try:
                # int() will round down which is what we want.
                qty += min([int(i.variation.inventory.physical() / i.quantity) for i in BundleVariation.objects.filter(umbrella=product)])
            except ValueError:
                pass
            # qty += min([i.inventory.physical() for i in product.bundle_variations.all()])

        return qty

    def salable(self):
        """Items that are available for sale"""
        if self._hints['instance'].product.always_on_stock:
            return 99999

        return self.physical() - self.reserved()

    def reserved(self):
        """Items that have been sold but not shipped"""
        sold_agg = self._hints['instance'].orderitem_set.\
            all().\
            exclude(
                order__status__in=Order.DONE_TYPES).\
            aggregate(Sum('quantity'))['quantity__sum'] or 0

        return sold_agg


class InventoryManager(MultiTenantManager):
    def get_queryset(self):
        return InventoryQuerySet(self.model, using=self._db)

    def salable(self):
        return self.get_queryset().salable()

    def physical(self):
        return self.get_queryset().physical()

    def reserved(self):
        return self.get_queryset().reserved()
