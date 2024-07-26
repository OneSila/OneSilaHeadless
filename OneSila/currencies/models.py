from core import models
from django.db.models import Q
from currencies.signals import exchange_rate_official__pre_save, \
    exchange_rate_official__post_save, exchange_rate__post_save, \
    exchange_rate__pre_save
from core.decorators import trigger_pre_and_post_save
from django.utils.translation import gettext_lazy as _


class PublicCurrency(models.SharedModel):
    iso_code = models.CharField(max_length=3)
    name = models.CharField(max_length=30)
    symbol = models.CharField(max_length=3)

    def __str__(self):
        return self.iso_code


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
    exchange_rate = models.FloatField(default=1, null=True, blank=True)
    exchange_rate_official = models.FloatField(default=1, null=True, blank=True)
    follow_official_rate = models.BooleanField(default=False)
    round_prices_up_to = models.IntegerField(default=1, null=True, blank=True)
    is_default_currency = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    @trigger_pre_and_post_save('exchange_rate', exchange_rate__pre_save, exchange_rate__post_save)
    @trigger_pre_and_post_save('exchange_rate_official', exchange_rate_official__pre_save, exchange_rate_official__post_save)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def set_exchange_rate_official(self, new_rate, force_save=False):
        self.exchange_rate_official = new_rate
        self.save(force_save=force_save)

    class Meta:
        search_terms = ['iso_code', 'name']
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')

        constraints = [
            models.UniqueConstraint(
                fields=['multi_tenant_company'],
                condition=Q(is_default_currency=True),
                name='unique_is_default_currency',
                violation_error_message=_("You can only have one default currency.")
            ),
            models.UniqueConstraint(
                fields=['iso_code', 'multi_tenant_company'],
                name='unique_iso_code_multi_tenant_company',
                violation_error_message=_("This currency already exists.")
            ),
        ]
