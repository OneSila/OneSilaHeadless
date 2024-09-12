from django.db.models import UniqueConstraint

from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.property import (
    RemoteProperty,
    RemotePropertySelectValue,
    RemoteProductProperty
)
from core import models
from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem
from django.utils.translation import gettext_lazy as _


class MagentoProperty(RemoteProperty):
    """
    Magento-specific model for remote properties.
    """
    attribute_code = models.CharField(
        max_length=255,
        help_text="The attribute code used in Magento for this property.",
        verbose_name="Attribute Code"
    )

    class Meta:
        verbose_name = 'Magento Property'
        verbose_name_plural = 'Magento Properties'
        # @TODO: Find out how to add unique constrain with sales channel
        # https://stackoverflow.com/questions/28799949/django-polymorphic-models-with-unique-together

class MagentoPropertySelectValue(RemotePropertySelectValue):
    """
    Magento-specific model for remote property select values.
    """
    pass


class MagentoProductProperty(RemoteProductProperty):
    """
    Magento-specific model for remote product properties.
    """
    pass


class MagentoAttributeSet(RemoteObjectMixin, models.Model):
    """
    Magento-specific model representing an attribute set.
    """

    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The local ProductPropertiesRule associated with this Magento attribute set."
    )
    group_remote_id = models.CharField(
        _('Group Remote ID'),
        max_length=256,
        null=True,
        help_text="The remote group ID associated with this attribute set in Magento."
    )

    class Meta:
        unique_together = ('local_instance', 'sales_channel')
        verbose_name = 'Magento Attribute Set'
        verbose_name_plural = 'Magento Attribute Sets'

    def __str__(self):
        try:
            return f"Magento attribute set for {self.local_instance.product_type}"
        except AttributeError:
            return self.safe_str


class MagentoAttributeSetAttribute(RemoteObjectMixin, models.Model):
    """
    Magento-specific model representing an attribute within an attribute set.
    """

    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The local ProductPropertiesRuleItem associated with this Magento attribute."
    )
    magento_rule = models.ForeignKey(
        MagentoAttributeSet,
        on_delete=models.CASCADE,
        help_text="The Magento attribute set to which this attribute belongs."
    )
    remote_property = models.ForeignKey(
        MagentoProperty,
        on_delete=models.PROTECT,
        help_text="The MagentoProperty associated with this attribute set attribute."
    )

    class Meta:
        unique_together = ('local_instance', 'magento_rule')
        verbose_name = 'Magento Attribute Set Attribute'
        verbose_name_plural = 'Magento Attribute Set Attributes'

    def __str__(self):
        try:
            return f"Attribute {self.local_instance.property.internal_name} in {self.magento_rule}"
        except AttributeError:
            return self.safe_str