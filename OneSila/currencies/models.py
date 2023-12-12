from core import models
from django.db.models import Q
from currencies.signals import exchange_rate_official__pre_save, \
    exchange_rate_official__post_save, exchange_rate__post_save, \
    exchange_rate__pre_save
from core.models import MultiTenantAwareMixin
from core.decorators import trigger_pre_and_post_save
from django.utils.translation import gettext_lazy as _

from datetime import datetime
from functools import wraps


class Currency(models.Model):
    '''
    Currencies determine the final price.

    Every price generated will be based on the inheritance, exchange rate and round_price_to.
    '''
    iso_code = models.CharField(max_length=3)
    name = models.CharField(max_length=30)
    symbol = models.CharField(max_length=3)

    inherits_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='passes_to')
    exchange_rate = models.FloatField(default=1)
    exchange_rate_official = models.FloatField(default=1)
    follow_official_rate = models.BooleanField(default=False)
    round_prices_up_to = models.IntegerField(default=1)
    is_default_currency = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    @trigger_pre_and_post_save('exchange_rate', exchange_rate__pre_save, exchange_rate__post_save)
    @trigger_pre_and_post_save('exchange_rate_official', exchange_rate_official__pre_save, exchange_rate_official__post_save)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def set_exchange_rate_official(new_rate, force_save=False):
        self.exchange_rate_official = new_rate
        self.save(force_save=force_save)

    class Meta:
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')

        constraints = [
            models.UniqueConstraint(
                fields=['is_default_currency'],
                condition=Q(is_default_currency=True),
                name='unique_is_default_currency')
        ]
