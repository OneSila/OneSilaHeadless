from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin
from django.db.models import Model as OldMOdel


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Model(TimeStampMixin, MultiTenantAwareMixin, OldMOdel):
    class Meta:
        abstract = True


class SharedModel(TimeStampMixin, OldMOdel):
    class Meta:
        abstract = True
