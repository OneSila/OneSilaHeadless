from core import models
from django.utils.translation import gettext_lazy as _

from properties.managers import PropertyManager, ProductPropertiesRuleManager
from translations.models import TranslationFieldsMixin, TranslatedModelMixin
from builtins import property as django_property  # in this file we will use property as django property because we have fields named property
from django.db.models import Q
from django.core.exceptions import ValidationError

class Property(TranslatedModelMixin, models.Model):
    """https://github.com/TweaveTech/django-classifier/blob/master/classifier/models.py"""
    class TYPES:
        INT = 'INT'
        FLOAT = 'FLOAT'
        TEXT = 'TEXT'
        DESCRIPTION = 'DESCRIPTION'
        BOOLEAN = 'BOOLEAN'
        DATE = 'DATE'
        DATETIME = 'DATETIME'
        SELECT = 'SELECT'
        MULTISELECT = 'MULTISELECT'

        ALL = (
            (INT, _('Integer')),
            (FLOAT, _('Float')),
            (TEXT, _('Text')),
            (DESCRIPTION, _('Description')),
            (BOOLEAN, _('Boolean')),
            (DATE, _('Date')),
            (DATETIME, _('Date time')),
            (SELECT, _('Select')),
            (MULTISELECT, _('Multi Select')),
        )

    type = models.CharField(
        max_length=20,
        choices=TYPES.ALL,
        verbose_name=_('Type of property'),
        db_index=True
    )
    is_public_information = models.BooleanField(default=True)
    add_to_filters = models.BooleanField(default=True)
    is_product_type = models.BooleanField(default=False)

    # advanced tab
    value_validator = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('Value validator'),
        help_text=_('Regex to validate value')
    )
    # the name that will be used in integration. Consider making it a foreign key with integrations in the future. for now is enough
    # it will be the snake case version of the name in default language "Product Type" => "product_type"
    internal_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Internal Name'))

    objects = PropertyManager()

    @django_property
    def name(self):
        return self._get_translated_value(field_name='name', related_name='propertytranslation_set')

    def delete(self, *args, **kwargs):
        # if self.is_product_type:
        #     raise ValidationError(_("Product type cannot be deleted."))
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk and self.is_dirty_field('is_product_type'):
            raise ValidationError(_("Product type cannot be changed after creation."))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.multi_tenant_company} -> {self.name}"

    class Meta:
        verbose_name_plural = _("Properties")
        search_terms = ['propertytranslation__name']
        constraints = [
            models.UniqueConstraint(
                fields=['multi_tenant_company'],
                condition=Q(is_product_type=True),
                name='unique_is_product_type',
                violation_error_message=_("You can only have one product type per multi-tenant company.")
            ),
        ]


class PropertyTranslation(TranslationFieldsMixin, models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name=_('Name'))

    class Meta:
        translated_field = 'property'
        search_terms = ['name']
        unique_together = ("name", "language", "multi_tenant_company")


class PropertySelectValue(TranslatedModelMixin, models.Model):
    property = models.ForeignKey(Property, on_delete=models.PROTECT)
    image = models.ForeignKey('media.Image', null=True, blank=True, on_delete=models.CASCADE)

    @django_property
    def value(self, language=None):
        return self._get_translated_value(field_name='value', related_name='propertyselectvaluetranslation_set', language=language)

    def __str__(self):
        return f"{self.value} <{self.property}>"

    class Meta:
        search_terms = ['propertyselectvaluetranslation__value']


class PropertySelectValueTranslation(TranslationFieldsMixin, models.Model):
    propertyselectvalue = models.ForeignKey(PropertySelectValue, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, verbose_name=_('Value'))

    class Meta:
        translated_field = 'propertyselectvalue'
        search_terms = ['value']
        unique_together = ("value", "language", "multi_tenant_company")  # added language as well because some words translates the same in different languages


class ProductProperty(TranslatedModelMixin, models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_int = models.IntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_select = models.ForeignKey(PropertySelectValue, on_delete=models.CASCADE, related_name='value_select_set', null=True, blank=True)
    value_multi_select = models.ManyToManyField(PropertySelectValue, related_name='value_multi_select_set', blank=True)

    def __str__(self):
        return f"{self.product} {self.property} > {self.get_value()}"

    def get_value(self):
        """
        Converts the various values and returns you the right type/value for the given property.
        """
        return getattr(self, 'get_value_{}'.format(self.property.type.lower()))()

    def get_value_int(self):
        return self.value_int

    def get_value_float(self):
        return self.value_float

    def get_value_text(self, language=None):
        return self._get_translated_value(field_name='value_text', related_name='productpropertytexttranslation_set', language=language)

    def get_value_description(self, language=None):
        return self._get_translated_value(field_name='value_description', related_name='productpropertytexttranslation_set', language=language)

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
        unique_together = ("product", "property")


class ProductPropertyTextTranslation(TranslationFieldsMixin, models.Model):
    product_property = models.ForeignKey(ProductProperty, on_delete=models.CASCADE)
    value_text = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Text'))
    value_description = models.TextField(null=True, blank=True, verbose_name=_('Description'))

    class Meta:
        translated_field = 'product_property'
        search_terms = ['value_text', 'value_description']
        unique_together = ("product_property", "language")


class ProductPropertiesRule(models.Model):
    product_type = models.ForeignKey(
        PropertySelectValue,
        on_delete=models.PROTECT,
        verbose_name=_('Product Type'),
    )

    objects = ProductPropertiesRuleManager()

    def __str__(self):
        return f"{self.product_type} <{self.multi_tenant_company}>"

    def save(self, *args, **kwargs):

        if not self.product_type.property.is_product_type:
            raise ValidationError(_("Invalid product type."))

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = _("Product Properties Rules")
        unique_together = ("product_type", "multi_tenant_company")


class ProductPropertiesRuleItem(models.Model):
    REQUIRED_IN_CONFIGURATOR = 'REQUIRED_IN_CONFIGURATOR'
    OPTIONAL_IN_CONFIGURATOR = 'OPTIONAL_IN_CONFIGURATOR'
    REQUIRED = 'REQUIRED'
    OPTIONAL = 'OPTIONAL'

    RULE_TYPES = [
        (REQUIRED_IN_CONFIGURATOR, _('Required in Configurator')),
        (OPTIONAL_IN_CONFIGURATOR, _('Optional in Configurator')),
        (REQUIRED, _('Required')),
        (OPTIONAL, _('Optional')),
    ]

    rule = models.ForeignKey(ProductPropertiesRule, related_name='items', on_delete=models.CASCADE, verbose_name=_('Rule'))
    property = models.ForeignKey(Property, on_delete=models.PROTECT, verbose_name=_('Property'))
    type = models.CharField(max_length=25, choices=RULE_TYPES, verbose_name=_('Type'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))

    def save(self, *args, **kwargs):
        # Ensure property is not a product type
        if self.property.is_product_type:
            raise ValidationError(_("Property cannot be a product type."))

        # Ensure that if type is REQUIRED_IN_CONFIGURATOR, property type must be SELECT or MULTISELECT
        if self.type in [self.REQUIRED_IN_CONFIGURATOR, self.OPTIONAL_IN_CONFIGURATOR] and self.property.type != Property.TYPES.SELECT:
            raise ValidationError(_("Property must be of type SELECT."))

        # Ensure rule cannot have OPTIONAL_IN_CONFIGURATOR without a REQUIRED_IN_CONFIGURATOR
        if self.type == self.OPTIONAL_IN_CONFIGURATOR and not self.rule.items.filter(type=self.REQUIRED_IN_CONFIGURATOR).exists():
            raise ValidationError(_("Cannot have optional in configurator without a required in configurator."))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.property} <{self.rule.product_type}>"

    class Meta:
        verbose_name_plural = _("Product Properties Rule Items")
        unique_together = ("property", "rule", "multi_tenant_company")
        ordering = ('sort_order',)
