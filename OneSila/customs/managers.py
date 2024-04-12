from core.managers import MultiTenantQuerySet, MultiTenantManager


class HsCodeQueryset(MultiTenantQuerySet):
    pass


class HsCodeManager(MultiTenantManager):
    def get_queryset(self):
        return HsCodeQueryset(self.model, using=self._db)
