from core.managers import MultiTenantQuerySet, MultiTenantManager
from django.db.models import Sum, F


class PurchaseOrderItemQuerySet(MultiTenantQuerySet):
    def total(self):
        return self.aggregate(
            total=Sum(F('quantity') * F('unit_price')))['total'] or 0


class PurchaseOrderItemManager(MultiTenantManager):
    def get_queryset(self):
        return PurchaseOrderItemQuerySet(self.model, using=self._db)

    def total(self):
        return self.get_queryset().total()
