from core.managers import MultiTenantQuerySet, MultiTenantManager
from products.product_types import HAS_DIRECT_INVENTORY_TYPES, HAS_INDIRECT_INVENTORY_TYPES
import logging
logger = logging.getLogger(__name__)


class LeadTimeQuerySet(MultiTenantQuerySet):
    def order_by_fastest(self):
        return self.order_by('unit', 'max_time', 'min_time')

    def get_product_leadtime(self, product):
        from .models import LeadTimeProductOutOfStock

        inventory_qs = product.inventory.filter_physical()
        leadtime = self.\
            filter_leadtimes_for_inventory(inventory_qs).\
            filter_fastest()

        if not leadtime:
            if product.type in HAS_DIRECT_INVENTORY_TYPES:
                try:
                    leadtime_product = LeadTimeProductOutOfStock.objects.get(product=product)
                    leadtime = leadtime_product.leadtime_outofstock
                except LeadTimeProductOutOfStock.DoesNotExist:
                    pass
            elif product.type in HAS_INDIRECT_INVENTORY_TYPES:
                supplier_products = product.supplier_products.all()
                leadtimes_outofstock_ids = LeadTimeProductOutOfStock.objects.\
                    filter(product__in=supplier_products).\
                    values('leadtime_outofstock')
                leadtimes = self.model.objects.filter(id__in=leadtimes_outofstock_ids, multi_tenant_company=product.multi_tenant_company)
                leadtime = leadtimes.filter_fastest()

        if not leadtime:
            raise self.model.DoesNotExist(f"No LeadTime found for Product.id {product.id}")

        return leadtime

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

    def get_product_leadtime(self, product):
        return self.get_queryset().get_product_leadtime(product=product)
