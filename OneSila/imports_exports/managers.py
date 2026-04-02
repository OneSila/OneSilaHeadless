from core.managers import MultiTenantManager, MultiTenantQuerySet
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet


class ImportQuerySet(PolymorphicQuerySet, MultiTenantQuerySet):
    """QuerySet for imports with polymorphic + search support."""


class ImportManager(PolymorphicManager, MultiTenantManager):
    """Manager for imports with polymorphic + search support."""

    def get_queryset(self):
        return ImportQuerySet(self.model, using=self._db)
