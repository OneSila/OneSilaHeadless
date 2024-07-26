from core import models
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin, TranslatedModelMixin


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
