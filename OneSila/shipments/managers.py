from core.managers import MultiTenantQuerySet, MultiTenantManager
from django.db.models import Case, F, When, Value, Sum


def get_orderitem(self, orderitem=None):
    from orders.models import OrderItem

    if not orderitem:
        orderitem = self._hints['instance']

    if not isinstance(orderitem, OrderItem):
        raise ValueError(f"OrderItem needed either through chaining or supplied.")

    return orderitem


class ShipmentItemQuerySet(MultiTenantQuerySet):
    def todo(self, orderitem=None):
        orderitem = get_orderitem(self, orderitem)
        qty = orderitem.quantity
        qty_done = self.done(orderitem)
        qty_in_progress = self.in_progress(orderitem)
        return qty - qty_done - qty_in_progress

    def in_progress(self, orderitem=None):
        from .models import Shipment

        orderitem = get_orderitem(self, orderitem)
        shipmentitem_qs = self.model.objects.\
            filter(
                orderitem=orderitem,
                multi_tenant_company=orderitem.multi_tenant_company,
                shipments__status__in=Shipment.IN_PROGRESS_STATUS_LIST).\
            distinct()
        return shipmentitem_qs.aggregate(qty_in_progress=Sum('quantity'))['qty_in_progress'] or 0

    def done(self, orderitem=None):
        from .models import Shipment

        orderitem = get_orderitem(self, orderitem)
        shipmentitem_qs = self.model.objects.\
            filter(
                orderitem=orderitem,
                multi_tenant_company=orderitem.multi_tenant_company,
                shipments__status__in=Shipment.DONE_STATUS_LIST).\
            distinct()
        return shipmentitem_qs.aggregate(qty_done=Sum('quantity'))['qty_done'] or 0


class ShipmentItemManager(MultiTenantManager):
    def get_queryset(self):
        return ShipmentItemQuerySet(self.model, using=self._db)

    def todo(self, orderitem=None):
        return self.get_queryset().todo(orderitem=None)

    def in_progress(self, orderitem=None):
        return self.get_queryset().in_progress(orderitem=None)

    def done(self, orderitem=None):
        return self.get_queryset().done(orderitem=None)
