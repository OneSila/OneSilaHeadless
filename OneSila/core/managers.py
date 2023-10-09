# from django_shared_multi_tenant.managers import MultiTenantManager, MultiTenantQuerySet
from django.db.models import QuerySet, Manager
from django.db import IntegrityError


class MultiTenantCompanyCreateMixin:
    def create(self, *args, **kwargs):
        multi_tenant_company = kwargs.get('multi_tenant_company')

        if not multi_tenant_company:
            raise IntegrityError("You cannot create without setting a multi_tenant_company value.")

        return super().create(*args, **kwargs)


class Manager(Manager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db)
