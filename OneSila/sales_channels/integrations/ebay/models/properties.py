from django.utils.translation import gettext_lazy as _

from core import models
from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    Property,
)
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import (
    RemoteProductProperty,
    RemoteProperty,
)
from sales_channels.integrations.ebay.constants import (
    EBAY_INTERNAL_PROPERTY_DEFAULTS,
)
from sales_channels.integrations.ebay.managers import (
    EbayInternalPropertyManager,
    EbayProductTypeManager,
    EbayPropertyManager,
    EbayPropertySelectValueManager,
)


class EbayProperty(RemoteProperty):
    """eBay attribute model holding marketplace specific metadata."""

    marketplace = models.ForeignKey(
        'ebay.EbaySalesChannelView',
        on_delete=models.CASCADE,
        related_name='properties',
        help_text="Marketplace in which this aspect definition applies.",
    )
    localized_name = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Localized aspect name as returned by eBay.",
    )
    translated_name = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Aspect name translated into the company language.",
    )
    allows_unmapped_values = models.BooleanField(
        default=False,
        help_text="Whether values outside eBay suggestions are accepted.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        default=Property.TYPES.TEXT,
        help_text="Mapped internal property type for this aspect.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original aspect metadata returned by eBay.",
    )
    value_format = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Format specification returned by eBay (aspectFormat).",
    )

    objects = EbayPropertyManager()

    class Meta:
        verbose_name = _("eBay Property")
        verbose_name_plural = _("eBay Properties")
        unique_together = ('marketplace', 'localized_name')
        search_terms = ['localized_name', 'translated_name', 'remote_id']


class EbayInternalProperty(RemoteObjectMixin, models.Model):
    """Static eBay property definitions used to build payloads."""

    local_instance = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Local property associated with this internal eBay field.",
    )
    code = models.CharField(
        max_length=255,
        help_text="Field code used when building eBay requests.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human readable label for the internal field.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        default=Property.TYPES.TEXT,
        help_text="Mapped internal property type for this field.",
    )
    is_root = models.BooleanField(
        default=False,
        help_text="Defines if the value belongs to the inventory item payload root.",
    )

    objects = EbayInternalPropertyManager()

    class Meta:
        verbose_name = _("eBay Internal Property")
        verbose_name_plural = _("eBay Internal Properties")
        constraints = [
            models.UniqueConstraint(
                fields=['sales_channel', 'code'],
                name='unique_ebay_internal_property_code_per_channel',
            )
        ]
        search_terms = ['code', 'name']

    def __str__(self):
        return f"{self.code} ({self.sales_channel})"



class EbayInternalPropertyOption(models.Model):
    """Allowed option for an eBay internal property."""

    internal_property = models.ForeignKey(
        EbayInternalProperty,
        on_delete=models.CASCADE,
        related_name='options',
        help_text="Internal property this option belongs to.",
    )
    sales_channel = models.ForeignKey(
        'ebay.EbaySalesChannel',
        on_delete=models.CASCADE,
        related_name='internal_property_options',
        help_text="Sales channel that owns this option.",
    )
    local_instance = models.ForeignKey(
        'properties.PropertySelectValue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional link to a local property select value mapped to this option.",
    )
    value = models.CharField(
        max_length=64,
        help_text="Remote enumeration value expected by eBay.",
    )
    label = models.CharField(
        max_length=255,
        help_text="Human readable label presented to users.",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description explaining when to use this value.",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order for this option.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate to hide the option from selection lists without deleting it.",
    )

    class Meta:
        verbose_name = _("eBay Internal Property Option")
        verbose_name_plural = _("eBay Internal Property Options")
        ordering = ('sort_order', 'label')
        unique_together = ('internal_property', 'value')
        search_terms = ['label', 'value', 'local_instance__propertyselectvaluetranslation__value']

    def __str__(self):
        return f"{self.value} @ {self.internal_property.code}"

    def save(self, *args, **kwargs):
        if self.internal_property_id:
            if not self.sales_channel_id:
                self.sales_channel_id = self.internal_property.sales_channel_id
            if not self.multi_tenant_company_id:
                self.multi_tenant_company_id = self.internal_property.multi_tenant_company_id
        super().save(*args, **kwargs)



class EbayPropertySelectValue(RemoteObjectMixin, models.Model):
    """eBay attribute value model with localization support."""

    ebay_property = models.ForeignKey(
        EbayProperty,
        on_delete=models.CASCADE,
        related_name='select_values',
        help_text="eBay property this value belongs to.",
    )
    marketplace = models.ForeignKey(
        'ebay.EbaySalesChannelView',
        on_delete=models.CASCADE,
        related_name='property_values',
        help_text="Marketplace in which this aspect value applies.",
    )
    local_instance = models.ForeignKey(
        'properties.PropertySelectValue',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Optional link to the local PropertySelectValue.",
    )
    localized_value = models.CharField(
        max_length=512,
        help_text="Localized aspect value as returned by eBay.",
    )
    translated_value = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Aspect value translated into the company language.",
    )

    objects = EbayPropertySelectValueManager()

    class Meta:
        verbose_name = _("eBay Property Value")
        verbose_name_plural = _("eBay Property Values")
        unique_together = ('ebay_property', 'marketplace', 'localized_value')
        search_terms = ['localized_value', 'translated_value', 'ebay_property__localized_name']

    def __str__(self):
        return f"{self.localized_value} ({self.marketplace})"


class EbayProductType(RemoteObjectMixin, models.Model):
    """eBay product type (category) representation."""

    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Local product type rule associated with this category.",
    )
    marketplace = models.ForeignKey(
        'ebay.EbaySalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_types',
        help_text="Marketplace in which this category applies.",
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Localized category name from eBay.",
    )
    translated_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Category name translated into the company language.",
    )
    imported = models.BooleanField(default=True)

    objects = EbayProductTypeManager()

    class Meta:
        verbose_name = _("eBay Product Type")
        verbose_name_plural = _("eBay Product Types")
        constraints = [
            models.UniqueConstraint(
                fields=['marketplace', 'remote_id'],
                condition=models.Q(remote_id__isnull=False),
                name='unique_ebayproducttype_remote_id_per_marketplace',
            ),
            models.UniqueConstraint(
                fields=['sales_channel', 'marketplace', 'local_instance'],
                condition=models.Q(local_instance__isnull=False),
                name='unique_ebayproducttype_local_rule_per_channel',
            ),
        ]
        search_terms = ['name', 'translated_name' ,'remote_id']

    def __str__(self):
        return self.name or self.safe_str


class EbayProductTypeItem(RemoteObjectMixin, models.Model):
    """eBay product type item linking a property to a category."""

    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Local product type rule item associated with this aspect.",
    )
    product_type = models.ForeignKey(
        EbayProductType,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="eBay product type this aspect belongs to.",
    )
    ebay_property = models.ForeignKey(
        EbayProperty,
        on_delete=models.CASCADE,
        related_name='product_type_items',
        help_text="eBay property associated with this product type item.",
    )
    remote_type = models.CharField(
        max_length=32,
        choices=ProductPropertiesRuleItem.RULE_TYPES,
        null=True,
        help_text="Requirement level for this aspect in eBay.",
    )

    class Meta:
        verbose_name = _("eBay Product Type Item")
        verbose_name_plural = _("eBay Product Type Items")
        unique_together = ('local_instance', 'product_type')


class EbayProductProperty(RemoteProductProperty):
    """eBay product property model."""

    pass
