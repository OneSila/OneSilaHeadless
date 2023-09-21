from django.db.models import *
from django.db import IntegrityError
from django_shared_multi_tenant.models import MultiTenantAwareMixin
from django.db.models import Model as OldModel


class TimeStampMixin(OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Model(TimeStampMixin, MultiTenantAwareMixin, OldModel):
    class Meta:
        abstract = True


class SharedModel(TimeStampMixin, OldModel):
    class Meta:
        abstract = True
