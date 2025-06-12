from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import (
    RemoteProperty,
    RemotePropertySelectValue,
    RemoteProductProperty,
)
from core import models
from django.utils.translation import gettext_lazy as _


class AmazonProperty(RemoteProperty):
    """Amazon specific remote property."""

    attribute_code = models.CharField(
        max_length=255,
        help_text="The attribute code used in Amazon for this property.",
        verbose_name="Attribute Code",
    )
    remote_name = models.CharField(
        max_length=255,
        help_text="The display label for the remote value (e.g., 'Red').",
        verbose_name="Remote Name",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Amazon Property'
        verbose_name_plural = 'Amazon Properties'


class AmazonPropertySelectValue(RemoteObjectMixin, models.Model):
    """Amazon-specific remote property select value with locale support."""

    amazon_property = models.ForeignKey(
        AmazonProperty,
        on_delete=models.CASCADE,
        related_name='select_values',
        help_text="The Amazon property this value belongs to."
    )
    marketplace = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        help_text="The Amazon marketplace for this value."
    )
    remote_value = models.CharField(
        max_length=255,
        help_text="The raw value from Amazon, in the marketplace's locale."
    )
    remote_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The display name of the value in the given locale."
    )
    local_instance = models.ForeignKey(
        'properties.PropertySelectValue',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional link to local PropertySelectValue."
    )

    class Meta:
        unique_together = ('amazon_property', 'marketplace', 'remote_value')

    def __str__(self):
        return f"{self.remote_name or self.remote_value} ({self.marketplace})"



class AmazonProductProperty(RemoteProductProperty):
    """Amazon specific remote product property."""

    class Meta:
        verbose_name_plural = _('Amazon Product Properties')


class AmazonProductType(RemoteObjectMixin, models.Model):
    """
    Amazon-specific model representing a product type (e.g., TOYS_AND_GAMES).
    """

    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The local ProductPropertiesRule associated with this Amazon product type."
    )
    category_code = models.CharField(
        _('Category Code'),
        max_length=256,
        null=True,
        help_text="The Amazon product type code (e.g., TOYS_AND_GAMES, CLOTHING)."
    )
    remote_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Display name for the Amazon product type (e.g., 'Toys & Games').",
        verbose_name="Remote Name"
    )

    class Meta:
        unique_together = ('local_instance', 'sales_channel')
        verbose_name = 'Amazon Product Type'
        verbose_name_plural = 'Amazon Product Types'

    def __str__(self):
        try:
            return f"Amazon product type for {self.local_instance.product_type} ({self.category_code}) @ {self.sales_channel}"
        except AttributeError:
            return f"{self.category_code} @ {self.sales_channel}"


class AmazonProductTypeItem(RemoteObjectMixin, models.Model):
    """
    Amazon-specific model representing an item within a product type.
    """

    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The local ProductPropertiesRuleItem associated with this Amazon product type item."
    )
    amazon_rule = models.ForeignKey(
        AmazonProductType,
        on_delete=models.CASCADE,
        help_text="The Amazon product type to which this item belongs."
    )
    remote_property = models.ForeignKey(
        AmazonProperty,
        on_delete=models.CASCADE,
        help_text="The AmazonProperty associated with this product type item."
    )
    remote_type = models.CharField(
        max_length=32,
        choices=ProductPropertiesRuleItem.RULE_TYPES,
        null=True,
        help_text="The type of requirement in Amazon."
    )

    class Meta:
        unique_together = ('local_instance', 'amazon_rule')
        verbose_name = 'Amazon Product Type Item'
        verbose_name_plural = 'Amazon Product Type Items'

    def __str__(self):
        try:
            return f"Item {self.local_instance.property.internal_name} ({self.remote_property.attribute_code}) in {self.amazon_rule}"
        except AttributeError:
            return self.safe_str