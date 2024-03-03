from core import models
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin


class Property(models.Model):
    """https://github.com/TweaveTech/django-classifier/blob/master/classifier/models.py"""
    class TYPES:
        INT = 'INT'
        FLOAT = 'FLOAT'
        STRING = 'STRING'
        TEXT = 'TEXT'
        BOOLEAN = 'BOOLEAN'
        DATE = 'DATE'
        DATETIME = 'DATETIME'
        SELECT = 'SELECT'
        MULTISELECT = 'MULTISELECT'

        ALL = (
            (INT, _('Integer')),
            (FLOAT, _('Float')),
            (STRING, _('String')),
            (STRING, _('Text')),
            (BOOLEAN, _('Boolean')),
            (DATE, _('Date')),
            (DATETIME, _('Date time')),
        )
    type = models.CharField(
        max_length=20,
        choices=TYPES.ALL,
        verbose_name=_('Type of property'),
        db_index=True
    )
    is_private_information = models.BooleanField(default=False)
    value_validator = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('Value validator'),
        help_text=_('Regex to validate value')
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Properties")


class PropertyTranslation(TranslationFieldsMixin, models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True, verbose_name=_('Name'))

    class Meta:
        search_terms = ['name']


class PropertySelectValue(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.value} <{self.property}>"


class PropertySelectValueTranslation(TranslationFieldsMixin, models.Model):
    propertyselectvalue = models.ForeignKey(PropertySelectValue, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, unique=True, verbose_name=_('Value'))


class ProductProperty(models.Model):
    # FIXME: This model needs to become translatable, more specifically:
    # - value_string
    # - value_text
    # - value_select <- Already translated
    # - value_multiselect <- Already translated
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_int = models.IntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_string = models.CharField(max_length=255, null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    value_select = models.ForeignKey(PropertySelectValue, on_delete=models.CASCADE, related_name='value_select_set')
    value_multi_select = models.ManyToManyField(PropertySelectValue, related_name='value_multi_select_set')

    def __str__(self):
        return f"{self.product} <{self.property}>"

    def get_value(self, value):
        """
        Converts the various values and returns you the right type/value for the given property.
        """
        value_type = self.property.value_type.lower()
        return getattr(self, 'get_value_{}'.format(value_type))()

    def get_value_int(self):
        return self.value_int

    def get_value_float(self):
        return self.value_float

    def get_value_string(self):
        return self.value_string

    def get_value_text(self):
        return self.value_text

    def get_value_boolean(self):
        return self.value_boolean

    def get_value_date(self):
        return self.value_date

    def get_value_datetime(self):
        return self.value_datetime

    def get_value_select(self):
        return self.value_select

    def get_value_multi_select(self):
        return self.value_multi_select

    class Meta:
        verbose_name_plural = _("Product Properties")
