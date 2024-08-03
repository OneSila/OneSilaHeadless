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
    def filter_physical(self, product=None):
        """ Return the inventories where a given product is located."""
        if product is None:
            product = self._hints['instance']

        multi_tenant_company = product.multi_tenant_company

        if product.type in HAS_DIRECT_INVENTORY_TYPES:
            return self.filter(quantity__gt=0, multi_tenant_company=multi_tenant_company)

        if product.type in HAS_INDIRECT_INVENTORY_TYPES:
            supplier_product_ids = product.supplier_products.\
                filter(multi_tenant_company=multi_tenant_company).\
                values('id')
            return self.model.objects.\
                filter(product_id__in=supplier_product_ids, multi_tenant_company=multi_tenant_company)

        if product.type in [BUNDLE]:
            # FIXME: What to do about bundle-products?  Nested? Or parts with querysets?
            raise Exception("Not implemented")

    def physical(self):
        """
        Physically on stock, could be reserved, could be salable.
        Configurable products return 0, as they cannot hold physical stock.
        """

        # Calculate your directly attached inventory (For manufacturable products)
        product = self._hints['instance']
        multi_tenant_company = product.multi_tenant_company

        if product.type in HAS_DIRECT_INVENTORY_TYPES or product.type in HAS_INDIRECT_INVENTORY_TYPES:
            inventory_qs = self.filter_physical()
            return inventory_qs.aggregate(Sum('quantity'))['quantity__sum'] or 0

        if product.type in [BUNDLE]:
            # Even though we can attach a variety of bundles, we must ensure we
            # dont sum them, but use min.  Why? Let's take an example. A bundle existing of a phone + 2 covers:
            # Phone: 100 items
            # Cover: 30
            # That means we can only ship 15x Phone+cover since the cover only has 30 pieces of which 2 are needed.
            qty = 0
            try:
                # int() will round down which is what we want.
                available_parts = []
                for through in BundleVariation.objects.filter(umbrella=product, multi_tenant_company=multi_tenant_company):
                    physical = through.variation.inventory.physical()
                    available_parts.append(int(physical / through.quantity))

                qty += min(available_parts)
            except ValueError:
                pass

        return qty

    def salable(self):
        """Items that are available for sale"""
        if self._hints['instance'].allow_backorder:
            return self.model._meta.backorder_item_count

        physical = self.physical()
        salable = physical - self.reserved()

        return salable

    def reserved(self):
        """Items that have been sold but not shipped"""
        product = self._hints['instance']
        multi_tenant_company = product.multi_tenant_company

        sold_agg = product.orderitem_set.\
            filter(multi_tenant_company=multi_tenant_company).\
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

    def filter_physical(self, product=None):
        return self.get_queryset().filter_physical(product=product)
