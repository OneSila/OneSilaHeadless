from core.managers.multi_tenant import MultiTenantQuerySet, MultiTenantManager
from django.db.models import Case, When, F, Value


class CurrencyQuerySet(MultiTenantQuerySet):
    def annotate_rate(self):
        return self.annotate(
            rate=Case(
                When(inherits_from__isnull=True, then=Value(1.0)),
                When(follow_official_rate=True, then=F("exchange_rate_official")),
                default=F("exchange_rate"),
            )
        )


class CurrencyManager(MultiTenantManager):
    def get_queryset(self):
        return CurrencyQuerySet(self.model, using=self._db).\
            annotate_rate()
