from __future__ import annotations

from django.core.exceptions import ValidationError

from core import models
from properties.models import ProductPropertiesRuleItem, Property, PropertySelectValue
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import RemoteProperty, RemotePropertySelectValue


class MiraklInternalProperty(RemoteObjectMixin, models.Model):
    """Mirakl internal/operator property definition."""

    local_instance = models.ForeignKey(
        "properties.Property",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local property associated with this internal Mirakl field.",
    )
    code = models.CharField(
        max_length=255,
        help_text="Field code used when building Mirakl payloads.",
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-readable name of the internal field.",
    )
    label = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Display label returned by Mirakl.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Mirakl description for the internal field.",
    )
    entity = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Mirakl entity the field belongs to.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        default=Property.TYPES.TEXT,
        help_text="Mapped local property type for this field.",
    )
    required = models.BooleanField(default=False)
    editable = models.BooleanField(default=False)
    accepted_values = models.JSONField(default=list, blank=True)
    regex = models.CharField(max_length=255, blank=True, default="")
    is_condition = models.BooleanField(
        default=False,
        help_text="True when this internal property represents Mirakl item condition.",
    )
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Internal Property"
        verbose_name_plural = "Mirakl Internal Properties"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "code"],
                name="unique_mirakl_internal_property_per_channel",
            ),
        ]
        search_terms = ["code", "name", "label"]

    def save(self, *args, **kwargs):
        self.remote_id = self.code
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.label or self.name or self.code


class MiraklInternalPropertyOption(models.Model):
    """Allowed option for a Mirakl internal property."""

    internal_property = models.ForeignKey(
        MiraklInternalProperty,
        on_delete=models.CASCADE,
        related_name="options",
    )
    sales_channel = models.ForeignKey(
        "mirakl.MiraklSalesChannel",
        on_delete=models.CASCADE,
        related_name="internal_property_options",
    )
    local_instance = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    value = models.CharField(max_length=255)
    label = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Mirakl Internal Property Option"
        verbose_name_plural = "Mirakl Internal Property Options"
        ordering = ("sort_order", "label")
        constraints = [
            models.UniqueConstraint(
                fields=["internal_property", "value"],
                name="unique_mirakl_internal_property_option_value",
            ),
        ]
        search_terms = ["value", "label"]

    def save(self, *args, **kwargs):
        if self.internal_property_id and not self.sales_channel_id:
            self.sales_channel_id = self.internal_property.sales_channel_id
        if self.internal_property_id and not self.multi_tenant_company_id:
            self.multi_tenant_company_id = self.internal_property.multi_tenant_company_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.label or self.value


class MiraklProperty(RemoteProperty):
    """Mirakl attribute definition."""

    allow_multiple = True

    code = models.CharField(max_length=255, help_text="Mirakl attribute code.")
    name = models.CharField(max_length=255, blank=True, default="", help_text="Mirakl attribute label.")
    description = models.TextField(blank=True, default="")
    required = models.BooleanField(default=False)
    variant = models.BooleanField(default=False)
    requirement_level = models.CharField(max_length=64, blank=True, default="")
    default_value = models.CharField(max_length=255, blank=True, default="")
    value_list_code = models.CharField(max_length=255, blank=True, default="")
    value_list_label = models.CharField(max_length=255, blank=True, default="")
    validations = models.JSONField(default=dict, blank=True)
    transformations = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Property"
        verbose_name_plural = "Mirakl Properties"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "code"],
                name="unique_mirakl_property_code_per_channel",
            ),
        ]
        search_terms = ["code", "name", "remote_id"]

    def save(self, *args, **kwargs):
        self.remote_id = self.code
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name or self.code


class MiraklProductTypeItem(RemoteObjectMixin, models.Model):
    """Link between Mirakl categories and Mirakl properties."""

    category = models.ForeignKey(
        "mirakl.MiraklCategory",
        on_delete=models.CASCADE,
        related_name="property_items",
    )
    property = models.ForeignKey(
        MiraklProperty,
        on_delete=models.CASCADE,
        related_name="category_items",
    )
    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    required = models.BooleanField(default=False)
    variant = models.BooleanField(default=False)
    role_data = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Product Type Item"
        verbose_name_plural = "Mirakl Product Type Items"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "property"],
                name="unique_mirakl_category_property_item",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.category_id and not self.sales_channel_id:
            self.sales_channel_id = self.category.sales_channel_id
        if self.category_id and not self.multi_tenant_company_id:
            self.multi_tenant_company_id = self.category.multi_tenant_company_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.category} > {self.property}"


class MiraklPropertyApplicability(RemoteObjectMixin, models.Model):
    """Channel applicability for a Mirakl property."""

    property = models.ForeignKey(
        MiraklProperty,
        on_delete=models.CASCADE,
        related_name="applicabilities",
    )
    view = models.ForeignKey(
        "mirakl.MiraklSalesChannelView",
        on_delete=models.CASCADE,
        related_name="property_applicabilities",
    )
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Property Applicability"
        verbose_name_plural = "Mirakl Property Applicabilities"
        constraints = [
            models.UniqueConstraint(
                fields=["property", "view"],
                name="unique_mirakl_property_applicability",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.property_id and not self.sales_channel_id:
            self.sales_channel_id = self.property.sales_channel_id
        if self.property_id and not self.multi_tenant_company_id:
            self.multi_tenant_company_id = self.property.multi_tenant_company_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.property} @ {self.view}"


class MiraklPropertySelectValue(RemotePropertySelectValue):
    """Mirakl selectable value for a property."""

    code = models.CharField(max_length=255, blank=True, default="")
    value = models.CharField(max_length=512, blank=True, default="")
    translated_value = models.CharField(max_length=512, blank=True, default="")
    value_list_code = models.CharField(max_length=255, blank=True, default="")
    value_list_label = models.CharField(max_length=255, blank=True, default="")
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta(RemotePropertySelectValue.Meta):
        verbose_name = "Mirakl Property Select Value"
        verbose_name_plural = "Mirakl Property Select Values"
        search_terms = ["code", "value", "translated_value", "remote_id"]

    def save(self, *args, **kwargs):
        self.remote_id = self.code or self.value
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.value or self.code or super().__str__()
