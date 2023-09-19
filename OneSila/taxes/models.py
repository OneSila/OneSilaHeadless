from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin


class Tax(MultiTenantAwareMixin, models.Model):
    '''
    Tax value class to assign taxes to products.  Will most likely
    only contain one value.  But should be here none the less.
    '''
    rate = models.IntegerField()
    name = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = '{}%'.format(self.rate)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'
