from core import models
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin, TranslatedModelMixin
from contacts.models import ShippingAddress


class LeadTime(TranslatedModelMixin, models.Model):
    HOUR = 'HOUR'
    DAY = 'DAY'
    WEEK = 'WEEK'
    MONTH = 'MONTH'

    UNIT_CHOICES = (
        (HOUR, _('Hour')),
        (DAY, _('Day')),
        (WEEK, _('Week')),
        (MONTH, _('Month')),
    )

    min_time = models.IntegerField()
    max_time = models.IntegerField()
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES)

    @property
    def name(self):
        return self._get_translated_value(field_name='name')

    def __str__(self):
        return f"{self.name}"

    class Meta:
        search_terms = ['translations__name']


class LeadTimeTranslation(TranslationFieldsMixin, models.Model):
    lead_time = models.ForeignKey(LeadTime, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.lead_time} <{self.language}>"

    class Meta:
        search_terms = ['name']
        unique_together = ['lead_time', 'language']


class LeadTimeForShippingAddress(models.Model):
    shippingaddress = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    leadtime = models.ForeignKey(LeadTime, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return f"{self.shippingaddress} <{self.leadtime.name}>"

    class Meta:
        unique_together = ['multi_tenant_company', 'shippingaddress', 'leadtime']
