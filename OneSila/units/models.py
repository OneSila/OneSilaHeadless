from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin


class Unit(MultiTenantAwareMixin, models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=5)

    def __str__(self):
        return self.unit
