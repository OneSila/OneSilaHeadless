from core.managers import MultiTenantQuerySet, MultiTenantManager

import logging
logger = logging.getLogger(__name__)


class LeadTimeQuerySet(MultiTenantQuerySet):
    def order_by_fastest(self):
        return self.order_by('unit', 'max_time', 'min_time')

    def get_product_leadtime(self, product):
        inventory_qs = product.inventory.physical_inventory_locations()
        return self.leadtime_for_inventorylocations(inventory_qs)

    def get_leadtimes_for_inventory(self, inventory_qs):
        from .models import LeadTimeForShippingAddress

        inventory_qs_vals = inventory_qs.values_list('id')
        logger.debug(f"Going to get leadtimes for {inventory_qs_vals=}")

        adresses_ids = inventory_qs.\
            filter(inventorylocation__shippingaddress__isnull=False).\
            values_list('inventorylocation__shippingaddress_id', flat=True)

        logger.debug(F"{adresses_ids=} discovered for {inventory_qs=}")

        leadtime_ids = LeadTimeForShippingAddress.objects.\
            filter(shippingaddress__in=adresses_ids).\
            values_list('leadtime_id', flat=True)
        leadtimes = self.filter(id__in=leadtime_ids)

        logging.debug(f"Discovered {leadtimes=} for {inventory_qs=}")
        return leadtimes

    def leadtime_for_inventorylocations(self, inventory_locations_qs):
        from inventory.models import Inventory
        logger.debug(f"Looking for fastest lead-time for {inventory_locations_qs=}")
        inventory_qs = Inventory.objects.filter(inventorylocation__in=inventory_locations_qs)
        leadtimes = self.get_leadtimes_for_inventory(inventory_qs)
        return self.filter_fastest(leadtimes)

    def filter_fastest(self, leadtimes=None):
        # In order to filter on fast, we need to order the
        # units.  Probably a numeric value is really what the right
        # way to go is. 1 is fast, 3 is slow.  Then we just need
        # to order by unit, max_time and min_time and grab the first one.
        if leadtimes is None:
            leadtimes = self

        if isinstance(leadtimes, list):
            leadtimes = self.model.objects.filter(id__in=leadtimes)

        logger.debug(f"We found following lead-times {leadtimes=}")

        return leadtimes.order_by_fastest().first()


class LeadTimeManager(MultiTenantManager):
    def get_queryset(self):
        return LeadTimeQuerySet(self.model, using=self._db)

    def filter_fastest(self, leadtimes=None):
        return self.get_queryset().filter_fastest(leadtimes=leadtimes)

    def order_by_fastest(self):
        return self.get_queryset().order_by_fastest()

    def leadtime_for_inventorylocations(self, inventory_locations_qs):
        return self.get_queryset().leadtime_for_inventorylocations(inventory_locations_qs=inventory_locations_qs)

    def get_product_leadtime(self, product):
        return self.get_queryset().get_product_leadtime(product=product)
