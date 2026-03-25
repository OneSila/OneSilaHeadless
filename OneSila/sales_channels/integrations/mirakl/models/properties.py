from __future__ import annotations

from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from core import models
from core.upload_paths import tenant_upload_to
from get_absolute_url.helpers import generate_absolute_url
from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem, Property, PropertySelectValue
from sales_channels.integrations.mirakl.managers import (
    MiraklProductTypeManager,
    MiraklPropertyManager,
    MiraklPropertySelectValueManager,
)
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.properties import RemoteProperty, RemotePropertySelectValue


class MiraklProperty(RemoteProperty):
    """Mirakl attribute definition."""

    allow_multiple = True

    REPRESENTATION_PROPERTY = "property"
    REPRESENTATION_UNIT = "unit"
    REPRESENTATION_DEFAULT_VALUE = "default_value"
    REPRESENTATION_PRODUCT_TITLE = "product_title"
    REPRESENTATION_PRODUCT_SUBTITLE = "product_subtitle"
    REPRESENTATION_PRODUCT_DESCRIPTION = "product_description"
    REPRESENTATION_PRODUCT_SHORT_DESCRIPTION = "product_short_description"
    REPRESENTATION_PRODUCT_BULLET_POINT = "product_bullet_point"
    REPRESENTATION_PRODUCT_SKU = "product_sku"
    REPRESENTATION_PRODUCT_INTERNAL_ID = "product_internal_id"
    REPRESENTATION_PRODUCT_CATEGORY = "product_category"
    REPRESENTATION_PRODUCT_CONFIGURABLE_SKU = "product_configurable_sku"
    REPRESENTATION_PRODUCT_CONFIGURABLE_ID = "product_configurable_id"
    REPRESENTATION_PRODUCT_ACTIVE = "product_active"
    REPRESENTATION_PRODUCT_URL_KEY = "product_url_key"
    REPRESENTATION_PRODUCT_EAN = "product_ean"
    REPRESENTATION_THUMBNAIL_IMAGE = "thumbnail_image"
    REPRESENTATION_SWATCH_IMAGE = "swatch_image"
    REPRESENTATION_IMAGE = "image"
    REPRESENTATION_VIDEO = "video"
    REPRESENTATION_DOCUMENT = "document"
    REPRESENTATION_PRICE = "price"
    REPRESENTATION_DISCOUNTED_PRICE = "discounted_price"
    REPRESENTATION_STOCK = "stock"
    REPRESENTATION_VAT_RATE = "vat_rate"
    REPRESENTATION_ALLOW_BACKORDER = "allow_backorder"
    REPRESENTATION_CONDITION = "condition"
    REPRESENTATION_LOGISTIC_CLASS = "logistic_class"

    REPRESENTATION_TYPE_CHOICES = [
        (REPRESENTATION_PROPERTY, "Property"),
        (REPRESENTATION_UNIT, "Unit"),
        (REPRESENTATION_DEFAULT_VALUE, "Default value"),
        (REPRESENTATION_PRODUCT_TITLE, "Product title"),
        (REPRESENTATION_PRODUCT_SUBTITLE, "Product subtitle"),
        (REPRESENTATION_PRODUCT_DESCRIPTION, "Product description"),
        (REPRESENTATION_PRODUCT_SHORT_DESCRIPTION, "Product short description"),
        (REPRESENTATION_PRODUCT_BULLET_POINT, "Product bullet point"),
        (REPRESENTATION_PRODUCT_SKU, "Product SKU"),
        (REPRESENTATION_PRODUCT_INTERNAL_ID, "Product internal ID"),
        (REPRESENTATION_PRODUCT_CATEGORY, "Product category"),
        (REPRESENTATION_PRODUCT_CONFIGURABLE_SKU, "Product configurable SKU"),
        (REPRESENTATION_PRODUCT_CONFIGURABLE_ID, "Product configurable ID"),
        (REPRESENTATION_PRODUCT_ACTIVE, "Product active"),
        (REPRESENTATION_PRODUCT_URL_KEY, "Product URL key"),
        (REPRESENTATION_PRODUCT_EAN, "Product EAN"),
        (REPRESENTATION_THUMBNAIL_IMAGE, "Thumbnail image"),
        (REPRESENTATION_SWATCH_IMAGE, "Swatch image"),
        (REPRESENTATION_IMAGE, "Image"),
        (REPRESENTATION_VIDEO, "Video"),
        (REPRESENTATION_DOCUMENT, "Document"),
        (REPRESENTATION_PRICE, "Price"),
        (REPRESENTATION_DISCOUNTED_PRICE, "Discounted price"),
        (REPRESENTATION_STOCK, "Stock"),
        (REPRESENTATION_VAT_RATE, "VAT rate"),
        (REPRESENTATION_ALLOW_BACKORDER, "Allow backorder"),
        (REPRESENTATION_CONDITION, "Condition"),
        (REPRESENTATION_LOGISTIC_CLASS, "Logistic class"),
    ]

    code = models.CharField(max_length=255, help_text="Mirakl attribute code.")
    name = models.CharField(max_length=255, blank=True, default="", help_text="Mirakl attribute label.")
    description = models.TextField(blank=True, default="")
    example = models.TextField(blank=True, default="")
    is_common = models.BooleanField(default=False)
    representation_type = models.CharField(
        max_length=64,
        choices=REPRESENTATION_TYPE_CHOICES,
        default=REPRESENTATION_PROPERTY,
    )
    language = models.CharField(max_length=64, null=True, blank=True, default=None)
    representation_type_decided = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True, default="")
    value_list_code = models.CharField(max_length=255, blank=True, default="")
    value_list_label = models.CharField(max_length=255, blank=True, default="")
    description_translations = models.JSONField(default=list, blank=True)
    label_translations = models.JSONField(default=list, blank=True)
    type_parameters = models.JSONField(default=list, blank=True)
    validations = models.JSONField(default=dict, blank=True)
    transformations = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    objects = MiraklPropertyManager()

    class Meta:
        verbose_name = "Mirakl Property"
        verbose_name_plural = "Mirakl Properties"
        search_terms = ["code", "name"]

    def save(self, *args, **kwargs):
        self.remote_id = self.code
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name or self.code


class MiraklProductType(RemoteObjectMixin, models.Model):
    """Mirakl product type used for local rule mapping."""

    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local product rule associated with this Mirakl product type.",
    )
    category = models.ForeignKey(
        "mirakl.MiraklCategory",
        on_delete=models.CASCADE,
        related_name="product_types",
        null=True,
        blank=True,
        help_text="Mirakl category this product type mirrors.",
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Mirakl product type label.",
    )
    template = models.FileField(
        upload_to=tenant_upload_to("mirakl_product_type_templates"),
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
    )
    imported = models.BooleanField(default=True)

    objects = MiraklProductTypeManager()

    class Meta:
        verbose_name = "Mirakl Product Type"
        verbose_name_plural = "Mirakl Product Types"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_id"],
                name="unique_mirakl_product_type_per_channel",
            ),
            models.UniqueConstraint(
                fields=["sales_channel", "local_instance"],
                condition=models.Q(local_instance__isnull=False),
                name="unique_mirakl_product_type_local_rule_per_channel",
            ),
        ]
        search_terms = ["remote_id", "name"]

    def save(self, *args, **kwargs):
        if self.category_id and not self.sales_channel_id:
            self.sales_channel_id = self.category.sales_channel_id
        if self.category_id and not self.multi_tenant_company_id:
            self.multi_tenant_company_id = self.category.multi_tenant_company_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name or self.remote_id or self.safe_str

    @property
    def ready_to_push(self) -> bool:
        return bool(self.template)

    @property
    def template_url(self) -> str | None:
        if not self.template:
            return None
        try:
            return f"{generate_absolute_url(trailing_slash=False)}{self.template.url}"
        except ValueError:
            return None


class MiraklProductTypeItem(RemoteObjectMixin, models.Model):
    """Link between Mirakl product types and Mirakl properties."""

    product_type = models.ForeignKey(
        "mirakl.MiraklProductType",
        on_delete=models.CASCADE,
        related_name="items",
    )
    remote_property = models.ForeignKey(
        MiraklProperty,
        on_delete=models.CASCADE,
        related_name="product_type_items",
    )
    local_instance = models.ForeignKey(
        ProductPropertiesRuleItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    hierarchy_code = models.CharField(max_length=255, blank=True, default="")
    required = models.BooleanField(default=False)
    variant = models.BooleanField(default=False)
    requirement_level = models.CharField(max_length=64, blank=True, default="")
    role_data = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Product Type Item"
        verbose_name_plural = "Mirakl Product Type Items"
        constraints = [
            models.UniqueConstraint(
                fields=["product_type", "remote_property"],
                name="unique_mirakl_product_type_property_item",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.product_type_id and not self.sales_channel_id:
            self.sales_channel_id = self.product_type.sales_channel_id
        if self.product_type_id and not self.multi_tenant_company_id:
            self.multi_tenant_company_id = self.product_type.multi_tenant_company_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product_type} > {self.remote_property}"


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
    label_translations = models.JSONField(default=list, blank=True)
    value_label_translations = models.JSONField(default=list, blank=True)
    value_list_code = models.CharField(max_length=255, blank=True, default="")
    value_list_label = models.CharField(max_length=255, blank=True, default="")
    raw_data = models.JSONField(default=dict, blank=True)

    objects = MiraklPropertySelectValueManager()

    class Meta(RemotePropertySelectValue.Meta):
        verbose_name = "Mirakl Property Select Value"
        verbose_name_plural = "Mirakl Property Select Values"
        search_terms = ["code", "value", "remote_id"]

    def save(self, *args, **kwargs):
        self.remote_id = self.code or self.value
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.value or self.code or super().__str__()
