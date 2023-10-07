# from django_shared_multi_tenant.managers import MultiTenantManager, MultiTenantQuerySet
from django.db.models import QuerySet, Manager


class QuerySet(QuerySet):
    pass


class Manager(Manager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db)
