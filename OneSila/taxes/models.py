from core import models
from django.utils.translation import gettext_lazy as _


class VatRate(models.Model):
    '''
    Tax value class to assign taxes to products.  Will most likely
    only contain one value.  But should be here none the less.

    These are not to be confused with the international rates one should charge eg in the euro-zone.
    although it is someting that needs to be concidered just the same: TODO
    '''
    name = models.CharField(max_length=3, null=True, blank=True)
    rate = models.IntegerField(help_text=_("VAT rate in percent.  Eg 21 for 21%"))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = '{}%'.format(self.rate)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'VAT Rate'
        verbose_name_plural = 'VAT Taxes'
