from core import models
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin, TranslatedModelMixin
from contacts.models import ShippingAddress
from .managers import LeadTimeManager


class LeadTime(TranslatedModelMixin, models.Model):
    HOUR = 1
    DAY = 2
    WEEK = 3
    MONTH = 4

    UNIT_CHOICES = (
        (HOUR, _('Hour')),
        (DAY, _('Day')),
        (WEEK, _('Week')),
        (MONTH, _('Month')),
    )

    min_time = models.IntegerField()
    max_time = models.IntegerField()
    unit = models.IntegerField(choices=UNIT_CHOICES)
    shippingaddresses = models.ManyToManyField(
        ShippingAddress,
        blank=True,
        through='LeadTimeForShippingAddress',
        symmetrical=False,
        related_name='leadtimes'
    )

    objects = LeadTimeManager()

    @property
    def name(self):
        return self._get_translated_value(field_name='name')

    def __str__(self):
        return f"{self.min_time} - {self.max_time} {self.get_unit_display()}(s)"

    class Meta:
        search_terms = ['translations__name']
        unique_together = ['multi_tenant_company', 'min_time', 'max_time', 'unit']


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
