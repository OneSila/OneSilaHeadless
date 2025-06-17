from django.db.models import JSONField

from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem, Property
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import (
    RemoteProperty,
    RemotePropertySelectValue,
    RemoteProductProperty,
)
from sales_channels.integrations.amazon.managers import (
    AmazonPropertyManager,
    AmazonPropertySelectValueManager,
    AmazonProductTypeManager,
)
from core import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone


class AmazonPublicDefinition(models.SharedModel):
    """
    Canonical, tenant-agnostic description of *one attribute key* of ONE
    product-type *in one Amazon API region*.

    Examples
    --------
    - api_region_code = "EU_DE"   product_type_code = "AIR_PURIFIER"
      code = "color"                          (simple)
    - api_region_code = "EU_FR"   product_type_code = "AIR_PURIFIER"
      code = "battery__cell_composition"      (composite, level-2)
    """

    # ------------- identity -------------
    api_region_code = models.CharField(max_length=8)          # "EU_DE"
    product_type_code = models.CharField(max_length=64)         # "AIR_PURIFIER"
    code = models.CharField(max_length=128)        # "color"  or "battery__cell_composition"

    # ------------- display -------------
    name = models.CharField(max_length=255)
    raw_schema = models.JSONField(blank=True, null=True)        # the slice of Amazon schema for this property

    # ------------- rendering / encoding -------------
    usage_definition = models.TextField(
        help_text=(
            "Template for rendering this attribute into SP-API payload.\n"
            "Tokens: %value%, %unit:weight%, %key:battery__cell_composition%, "
            "%marketplace_id%, %language_tag%"
        )
    )
    export_definition = models.JSONField(blank=True, null=True)

    last_fetched = models.DateTimeField(null=True, blank=True)

    is_required = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=False)

    def should_refresh(self):
        if not self.last_fetched:
            return True
        return timezone.now() - self.last_fetched > timedelta(days=180)

    class Meta:
        verbose_name = _("Amazon Public Definition")
        verbose_name_plural = _("Amazon Public Definitions")
        unique_together = (
            "api_region_code", "product_type_code", "code",
        )
        indexes = [
            models.Index(fields=["api_region_code"]),
            models.Index(fields=["product_type_code"]),
        ]

    def __str__(self):
        return f"[{self.api_region_code}] {self.product_type_code} :: {self.code}"


class AmazonProperty(RemoteProperty):
    """Amazon specific remote property."""

    code = models.CharField(
        max_length=255,
        help_text="The attribute code used in Amazon for this property.",
        verbose_name="Attribute Code",
    )

    name = models.CharField(
        max_length=255,
        help_text="The display label for the remote value (e.g., 'Red').",
        verbose_name="Remote Name",
        null=True,
        blank=True,
    )

    allows_unmapped_values = models.BooleanField(default=False)
    type = models.CharField(max_length=16, choices=Property.TYPES.ALL, default=Property.TYPES.TEXT)

    objects = AmazonPropertyManager()

    class Meta:
        verbose_name = 'Amazon Property'
        verbose_name_plural = 'Amazon Properties'
        search_terms = ['name', 'code']


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

    objects = AmazonPropertySelectValueManager()

    class Meta:
        unique_together = ('amazon_property', 'marketplace', 'remote_value')
        search_terms = [
            'remote_name',
            'remote_value',
            'amazon_property__name',
            'amazon_property__code',
        ]

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
    product_type_code = models.CharField(
        _('Category Code'),
        max_length=256,
        null=True,
        help_text="The Amazon product type code (e.g., TOYS_AND_GAMES, CLOTHING)."
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Display name for the Amazon product type (e.g., 'Toys & Games').",
        verbose_name="Remote Name"
    )

    objects = AmazonProductTypeManager()

    class Meta:
        unique_together = ('local_instance', 'sales_channel')
        verbose_name = 'Amazon Product Type'
        verbose_name_plural = 'Amazon Product Types'
        search_terms = ['name', 'product_type_code']

    def __str__(self):
        try:
            return f"Amazon product type for {self.local_instance.product_type} ({self.product_type_code}) @ {self.sales_channel}"
        except AttributeError:
            return f"{self.product_type_code} @ {self.sales_channel}"


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
