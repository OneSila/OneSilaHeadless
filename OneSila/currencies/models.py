from core import models
from django.db.models import Q
from django_shared_multi_tenant.models import MultiTenantAwareMixin
from django.utils.translation import gettext_lazy as _


class Currency(models.Model):
    '''
    Currencies determin the final price.

    Every price generated will be based on the inheritance, exchange rate and round_price_to.
    '''
    iso_code = models.CharField(max_length=3)
    name = models.CharField(max_length=30)
    symbol = models.CharField(max_length=3)

    inherits_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='passes_to')
    exchange_rate = models.FloatField(default=1)
    round_prices_up_to = models.IntegerField(default=1)

    is_default_currency = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')

        constraints = [
            models.UniqueConstraint(
                fields=['is_default_currency'],
                condition=Q(is_default_currency=True),
                name='unique_is_default_currency')
        ]
