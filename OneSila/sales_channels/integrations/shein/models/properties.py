"""Models representing Shein product type attributes and metadata."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from django.utils.translation import gettext_lazy as _

from core import models
from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    Property,
)
from sales_channels.integrations.shein.managers import SheinPropertyManager, SheinInternalPropertyManager, \
    SheinPropertySelectValueManager, SheinProductTypeManager
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import (
    RemoteProperty,
    RemotePropertySelectValue,
)


class SheinProperty(RemoteProperty):
    """Remote attribute shared across Shein product types."""

    class ValueModes(models.TextChoices):
        MANUAL_INTEGER = "manual_integer", _("Manual positive integer input")
        MULTI_SELECT = "multi_select", _("Dropdown multi-select")
        SALES_SINGLE_SELECT = "sales_single_select", _("Sales attribute single select")
        SINGLE_SELECT = "single_select", _("Single select")
        MULTI_SELECT_WITH_CUSTOM = "multi_select_with_custom", _("Multi-select with custom input")

        @classmethod
        def from_remote(cls, *, raw_value: Any) -> str:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                return cls.SINGLE_SELECT

            return {
                0: cls.MANUAL_INTEGER,
                1: cls.MULTI_SELECT,
                2: cls.SALES_SINGLE_SELECT,
                3: cls.SINGLE_SELECT,
                4: cls.MULTI_SELECT_WITH_CUSTOM,
            }.get(value, cls.SINGLE_SELECT)

    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Localized attribute name returned by Shein.",
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="English attribute name returned by Shein.",
    )
    value_mode = models.CharField(
        max_length=32,
        choices=ValueModes.choices,
        default=ValueModes.SINGLE_SELECT,
        help_text="Input mode Shein expects for this attribute.",
    )
    value_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of selectable values when applicable.",
    )
    attribute_source = models.IntegerField(
        null=True,
        blank=True,
        help_text="Source flag reported by Shein.",
    )
    data_dimension = models.IntegerField(
        null=True,
        blank=True,
        help_text="Data dimension flag returned by Shein.",
    )
    business_mode = models.IntegerField(
        null=True,
        blank=True,
        help_text="Business mode flag describing how the attribute is used.",
    )
    is_sample = models.BooleanField(
        default=False,
        help_text="Marks whether the attribute belongs to sample metadata.",
    )
    supplier_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Supplier identifier when Shein scopes the attribute to a supplier.",
    )
    attribute_doc = models.TextField(
        blank=True,
        default="",
        help_text="Markdown/HTML documentation snippet returned by Shein.",
    )
    attribute_doc_images = models.JSONField(
        default=list,
        blank=True,
        help_text="Image references associated with the attribute documentation.",
    )
    allows_unmapped_values = models.BooleanField(
        default=False,
        help_text="Whether merchants can submit custom attribute values for this attribute.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        default=Property.TYPES.TEXT,
        help_text="Mapped internal property type derived from Shein metadata.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original attribute payload returned by Shein.",
    )

    objects = SheinPropertyManager()

    class Meta:
        verbose_name = "Shein Property"
        verbose_name_plural = "Shein Properties"
        search_terms = ["remote_id", "name", "name_en"]

    def __str__(self) -> str:
        label = self.name or self.name_en or self.remote_id or "Unknown"
        return f"{label} ({self.remote_id})" if self.remote_id else label

    @staticmethod
    def determine_property_type(
        *,
        attribute_mode: Optional[int],
    ) -> str:
        try:
            value = int(attribute_mode) if attribute_mode is not None else None
        except (TypeError, ValueError):
            value = None

        if value == 0:
            return Property.TYPES.INT
        if value in {1, 4}:
            return Property.TYPES.MULTISELECT
        if value in {2, 3}:
            return Property.TYPES.SELECT
        return Property.TYPES.TEXT

    @staticmethod
    def allows_custom_values(*, attribute_mode: Optional[int]) -> bool:
        try:
            value = int(attribute_mode) if attribute_mode is not None else None
        except (TypeError, ValueError):
            return False
        return value in {0, 4}


class SheinPropertySelectValue(RemotePropertySelectValue):
    """Remote enumeration for a Shein attribute option."""

    value = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Localized attribute value returned by Shein.",
    )
    value_en = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="English translation for the attribute value.",
    )
    is_custom_value = models.BooleanField(
        default=False,
        help_text="True when Shein marks the value as user defined.",
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Visibility flag returned by Shein for the value.",
    )
    supplier_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Supplier identifier for scoped attribute values.",
    )
    documentation = models.TextField(
        blank=True,
        default="",
        help_text="Optional documentation snippet returned for the value.",
    )
    documentation_images = models.JSONField(
        default=list,
        blank=True,
        help_text="Image references associated with the value documentation.",
    )
    group_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Grouping metadata returned by Shein.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original attribute value payload returned by Shein.",
    )

    objects = SheinPropertySelectValueManager()

    class Meta(RemotePropertySelectValue.Meta):
        verbose_name = "Shein Property Select Value"
        verbose_name_plural = "Shein Property Select Values"
        search_terms = ["remote_id", "value", "value_en", "remote_property__name"]

    def __str__(self) -> str:
        label = self.value or self.value_en or self.remote_id or "Unknown"
        return f"{label} ({self.remote_property})"


class SheinProductType(RemoteObjectMixin, models.Model):
    """Leaf category metadata used to map to local product rules."""

    category_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Remote Shein category identifier associated with this product type.",
    )
    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local product properties rule mapped to this Shein product type.",
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Human readable name reported by Shein for the category/product type.",
    )
    translated_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Human readable name reported by Shein for the category/product type.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original payload returned by Shein for this product type.",
    )
    imported = models.BooleanField(
        default=True,
        help_text="Indicates whether the product type was fetched from Shein.",
    )

    objects = SheinProductTypeManager()

    class Meta:
        verbose_name = "Shein Product Type"
        verbose_name_plural = "Shein Product Types"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_id"],
                condition=models.Q(remote_id__isnull=False),
                name="unique_shein_product_type_per_channel",
            ),
            models.UniqueConstraint(
                fields=["sales_channel", "category_id"],
                condition=models.Q(category_id__gt=""),
                name="unique_shein_product_type_per_category",
            ),
        ]
        search_terms = ["remote_id", "name", "category_id"]

    def __str__(self) -> str:
        label = self.name or self.remote_id or "Unknown"
        return f"{label} ({self.remote_id})" if self.remote_id else label


class SheinProductTypeItem(RemoteObjectMixin, models.Model):
    """Mapping between a Shein product type and one of its attributes."""

    class Visibility(models.TextChoices):
        DISPLAY = "display", _("Display to shoppers")
        HIDDEN = "hidden", _("Hidden from shoppers")

        @classmethod
        def from_remote(cls, *, raw_value: Any) -> str:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                return cls.DISPLAY
            return {
                1: cls.DISPLAY,
                2: cls.HIDDEN,
            }.get(value, cls.DISPLAY)

    class AttributeType(models.TextChoices):
        SALES = "sales", _("Sales attribute")
        SIZE = "size", _("Size attribute")
        COMPOSITION = "composition", _("Composition attribute")
        COMMON = "common", _("Common attribute")

        @classmethod
        def from_remote(cls, *, raw_value: Any) -> str:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                return cls.COMMON
            return {
                1: cls.SALES,
                2: cls.SIZE,
                3: cls.COMPOSITION,
                4: cls.COMMON,
            }.get(value, cls.COMMON)

    class Requirement(models.TextChoices):
        NOT_FILLABLE = "not_fillable", _("Not fillable")
        OPTIONAL = "optional", _("Optional")
        REQUIRED = "required", _("Required")

        @classmethod
        def from_remote(cls, *, raw_value: Any) -> str:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                return cls.OPTIONAL
            return {
                1: cls.NOT_FILLABLE,
                2: cls.OPTIONAL,
                3: cls.REQUIRED,
            }.get(value, cls.OPTIONAL)

    class RemarkTags(models.TextChoices):
        IMPORTANT = "important", _("Important")
        COMPLIANCE = "compliance", _("Compliance")
        QUALITY = "quality", _("Quality")
        CUSTOMS = "customs", _("Customs")

        @classmethod
        def normalize(cls, *, values: Any) -> list[str]:
            if not isinstance(values, Iterable):
                return []
            normalized: list[str] = []
            for value in values:
                try:
                    numeric = int(value)
                except (TypeError, ValueError):
                    continue
                mapped = {
                    1: cls.IMPORTANT,
                    2: cls.COMPLIANCE,
                    3: cls.QUALITY,
                    4: cls.CUSTOMS,
                }.get(numeric)
                if mapped and mapped not in normalized:
                    normalized.append(mapped)
            return normalized

    product_type = models.ForeignKey(
        'shein.SheinProductType',
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Shein product type linked to this attribute.",
    )
    property = models.ForeignKey(
        'shein.SheinProperty',
        on_delete=models.CASCADE,
        related_name='product_type_items',
        help_text="Shein attribute definition referenced by this item.",
    )
    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local product rule item mapped to this Shein attribute, when available.",
    )
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.DISPLAY,
        help_text="Whether the attribute is shown to shoppers for this product type.",
    )
    attribute_type = models.CharField(
        max_length=16,
        choices=AttributeType.choices,
        default=AttributeType.COMMON,
        help_text="How Shein expects the attribute to be sent in payloads.",
    )
    requirement = models.CharField(
        max_length=16,
        choices=Requirement.choices,
        default=Requirement.OPTIONAL,
        help_text="Requirement level of the attribute for this product type.",
    )
    is_main_attribute = models.BooleanField(
        default=False,
        help_text="True when Shein marks the attribute as the main SKC attribute.",
    )
    allows_unmapped_values = models.BooleanField(
        default=False,
        help_text="True when Shein allows custom values for this attribute on the given category.",
    )
    remarks = models.JSONField(
        default=list,
        blank=True,
        help_text="Scenario tags (important/compliance/etc.) associated with the attribute.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original attribute configuration payload for this product type.",
    )

    class Meta:
        verbose_name = "Shein Product Type Item"
        verbose_name_plural = "Shein Product Type Items"
        constraints = [
            models.UniqueConstraint(
                fields=["product_type", "property"],
                name="unique_shein_product_type_attribute",
            )
        ]
        search_terms = ["property__name", "product_type__name"]

    def __str__(self) -> str:
        return f"{self.product_type} :: {self.property}"


class SheinInternalProperty(RemoteObjectMixin, models.Model):
    """Static Shein field definitions required when publishing listings."""

    local_instance = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local property associated with this Shein field.",
    )
    code = models.CharField(
        max_length=255,
        help_text="Shein internal field identifier (e.g. brand_code).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human readable label for the field.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        default=Property.TYPES.TEXT,
        help_text="Mapped internal property type for this field.",
    )
    is_root = models.BooleanField(
        default=False,
        help_text="True when the value lives at the root of the payload.",
    )
    payload_field = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Field name used when constructing the Shein payload.",
    )

    objects = SheinInternalPropertyManager()

    class Meta:
        verbose_name = _("Shein Internal Property")
        verbose_name_plural = _("Shein Internal Properties")
        constraints = [
            models.UniqueConstraint(
                fields=['sales_channel', 'code'],
                name='unique_shein_internal_property_code_per_channel',
            )
        ]
        search_terms = ['code', 'name']

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.code} ({self.sales_channel})"


class SheinInternalPropertyOption(models.Model):
    """Enumeration option for a Shein internal property (e.g. brand list)."""

    internal_property = models.ForeignKey(
        SheinInternalProperty,
        on_delete=models.CASCADE,
        related_name='options',
        help_text="Internal property this option belongs to.",
    )
    sales_channel = models.ForeignKey(
        'shein.SheinSalesChannel',
        on_delete=models.CASCADE,
        related_name='internal_property_options',
        help_text="Sales channel that owns this option.",
    )
    local_instance = models.ForeignKey(
        'properties.PropertySelectValue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional link to a local property select value.",
    )
    value = models.CharField(
        max_length=64,
        help_text="Remote enumeration value expected by Shein.",
    )
    label = models.CharField(
        max_length=255,
        help_text="Human readable label presented to users.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional description explaining when to use this value.",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order for this option.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate to hide the option without deleting it.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw payload returned by Shein for this option.",
    )

    class Meta:
        verbose_name = _("Shein Internal Property Option")
        verbose_name_plural = _("Shein Internal Property Options")
        ordering = ('sort_order', 'label')
        unique_together = ('internal_property', 'value')
        search_terms = ['label', 'value', 'local_instance__propertyselectvaluetranslation__value']

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.value} @ {self.internal_property.code}"

    def save(self, *args, **kwargs):
        if self.internal_property_id:
            if not self.sales_channel_id:
                self.sales_channel_id = self.internal_property.sales_channel_id
            if not self.multi_tenant_company_id:
                self.multi_tenant_company_id = self.internal_property.multi_tenant_company_id
        super().save(*args, **kwargs)