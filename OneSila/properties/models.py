from django.db import models
from django_shared_multi_tenant.models import MultiTenantAwareMixin
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin


class Property(MultiTenantAwareMixin, models.Model):
    """https://github.com/TweaveTech/django-classifier/blob/master/classifier/models.py"""
    class TYPES:
        INT = 'INT'
        FLOAT = 'FLOAT'
        STRING = 'STRING'
        BOOLEAN = 'BOOLEAN'
        DATE = 'DATE'
        DATETIME = 'DATETIME'
        SELECT = 'SELECT'
        MULTISELECT = 'MULTISELECT'

        ALL = (
            (INT, _('Integer')),
            (FLOAT, _('Float')),
            (STRING, _('String')),
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
    value_validator = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('Value validator'),
        help_text=_('Regex to validate value')
    )

    def __str__(self):
        return self.name


class PropertyTranslations(MultiTenantAwareMixin, TranslationFieldsMixin, models.Model)


property = models.ForeignKey(Property)
name = models.CharField(max_length=200, unique=True, verbose_name=_('Name'))


class PropertySelectValue(MultiTenantAwareMixin, models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.value} <{self.property}>"


class ProductProperty(MultiTenantAwareMixin, models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    value = models.CharField(max_length=20)
    value_select = models.ForeignKey(PropertySelectValue, on_delete=models.CASCADE)
    value_multi_select = models.ManyToManyField(PropertySelectValue)

    def __str__(self):
        return f"{self.product} <{self.property}>"

    def get_value(self, value):
        """
        run convertor from string to type in ``value_type`` field
        """
        value_type = self.property.value_type.lower()
        cleaner = getattr(self, 'get_value_{}'.format(value_type))
        return cleaner(value)

    @staticmethod
    def get_value_int(value):
        return int(value)

    @staticmethod
    def get_value_float(value):
        return float(value)

    @staticmethod
    def get_value_string(value):
        return six.text_type(value)

    @staticmethod
    def get_value_boolean(value):
        value_lower = self.value.lower()

        if value_lower in ['on', 'yes', 'true']:
            return True
        elif value_lower in ['off', 'no', 'false']:
            return False

        raise ValueError(_('Can\'t convert "{}" to boolean'.format(value)))

    @staticmethod
    def to_python_date(value):
        date = parse_date(value)
        if value and not date:
            raise ValueError('Can\'t convert "{}" to date'.format(value))

        return date

    @staticmethod
    def to_python_datetime(value):
        datetime = parse_datetime(value)
        if value and not datetime:
            raise ValueError('Can\'t convert "{}" to datetime'.format(value))

        return datetime

    @staticmethod
    def to_python_select(value):
        return self.value_select

    @staticmethod
    def to_python_multi_select(value):
        return self.value_multi_select
