from core.managers import MultiTenantQuerySet, MultiTenantManager
from products.product_types import HAS_DIRECT_INVENTORY_TYPES, \
    HAS_INDIRECT_INVENTORY_TYPES, BUNDLE
from products.models import BundleVariation

import logging
logger = logging.getLogger(__name__)


class LeadTimeQuerySet(MultiTenantQuerySet):
    def order_by_fastest(self):
        return self.order_by('unit', 'max_time', 'min_time')

    def filter_leadtimes_for_inventory(self, inventory_qs):
        from .models import LeadTimeForShippingAddress

        adresses_ids = inventory_qs.\
            filter(inventorylocation__shippingaddress__isnull=False).\
            values('inventorylocation__shippingaddress_id')

        leadtime_ids = LeadTimeForShippingAddress.objects.\
            filter(shippingaddress__in=adresses_ids).\
            values('leadtime_id')
        leadtimes = self.filter(id__in=leadtime_ids)

        return leadtimes

    def filter_fastest(self, leadtimes=None):
        # In order to filter on fast, we need to order the
        # units, a numeric value is really what the right
        # way to go is. 1 is fast, 3 is slow.  Then we just need
        # to order by unit, max_time and min_time and grab the first one.
        if leadtimes is None:
            leadtimes = self

        if isinstance(leadtimes, list):
            leadtimes = self.model.objects.filter(id__in=leadtimes)

        return leadtimes.order_by_fastest().first()

    def filter_slowest(self, leadtimes=None):
        # We can just order by fastest and take the last.
        if leadtimes is None:
            leadtimes = self

        if isinstance(leadtimes, list):
            leadtimes = self.model.objects.filter(id__in=leadtimes)

        return leadtimes.order_by_fastest().last()


class LeadTimeManager(MultiTenantManager):
    def get_queryset(self):
        return LeadTimeQuerySet(self.model, using=self._db)

    def filter_fastest(self, leadtimes=None):
        return self.get_queryset().filter_fastest(leadtimes=leadtimes)

    def filter_slowest(self, leadtimes=None):
        return self.get_queryset().filter_slowest(leadtimes=leadtimes)

    def order_by_fastest(self):
        return self.get_queryset().order_by_fastest()
