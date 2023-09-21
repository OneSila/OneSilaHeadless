from django.db import models


class Tax(models.Model):
    '''
    Tax value class to assign taxes to products.  Will most likely
    only contain one value.  But should be here none the less.

    These are not to be confused with the international rates one should charge eg in the euro-zone.
    although it is someting that needs to be concidered just the same: TODO
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
