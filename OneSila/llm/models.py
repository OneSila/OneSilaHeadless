import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core import models
from core.helpers import ensure_serializable, get_languages
from core.locales import LANGUAGE_MAX_LENGTH
from imports_exports.models import Import


class McpApiKey(models.SharedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcp_api_key")
    key = models.CharField(max_length=64, unique=True, db_index=True, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "MCP API Key"
        verbose_name_plural = "MCP API Keys"

    def __str__(self):
        return f"MCP API Key ({self.user})"

    @staticmethod
    def generate_key() -> str:
        return secrets.token_hex(32)

    @property
    def masked_key(self) -> str:
        if not self.key:
            return ""
        return f"{self.key[:4]}...{self.key[-4:]}"

    def regenerate_key(self, *, save=True) -> str:
        self.key = self.generate_key()
        if save:
            self.save(update_fields=["key", "updated_at"])
        return self.key

    def activate(self, *, save=True) -> None:
        self.is_active = True
        if save:
            self.save(update_fields=["is_active", "updated_at"])

    def deactivate(self, *, save=True) -> None:
        self.is_active = False
        if save:
            self.save(update_fields=["is_active", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)


class McpToolRun(Import, models.Model):
    MAX_JSON_VALUE_LENGTH = 20_000
    TRUNCATED_SUFFIX = "...[truncated]"
    OMITTED_IMAGE_CONTENT_TEMPLATE = "<image_content omitted, length={length}>"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcp_tool_runs")
    tool_name = models.CharField(
        max_length=128,
        db_index=True,
        help_text="MCP tool name that created this run, for example create_products or upsert_products.",
    )
    payload_content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Normalized MCP tool payload stored for traceability. Long values are truncated before saving.",
    )
    response_content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Lean MCP tool response payload stored for traceability. Long values are truncated before saving.",
    )
    assigned_views = models.ManyToManyField(
        "sales_channels.SalesChannelView",
        blank=True,
        related_name="mcp_tool_runs",
        help_text="Website/storefront views explicitly referenced by this MCP tool run, when applicable.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "MCP Tool Run"
        verbose_name_plural = "MCP Tool Runs"
        search_terms = ["name", "tool_name"]

    def __str__(self):
        display_name = self.name or self.tool_name or "MCP Tool Run"
        owner = self.user if self.user_id else "unassigned"
        return f"{display_name} - {owner} - {self.get_status_display()} ({self.percentage}%)"

    def user_full_name(self, info=None):
        user = getattr(self, "user", None)
        if user is None:
            return None
        return user.full_name()

    @classmethod
    def sanitize_json_content(cls, *, value):
        return cls._truncate_json_values(value=ensure_serializable(value))

    @classmethod
    def _truncate_json_values(cls, *, value, parent_key: str | None = None):
        if isinstance(value, dict):
            return {
                key: cls._truncate_json_values(value=item_value, parent_key=str(key))
                for key, item_value in value.items()
            }
        if isinstance(value, list):
            return [cls._truncate_json_values(value=item, parent_key=parent_key) for item in value]
        if isinstance(value, tuple):
            return [cls._truncate_json_values(value=item, parent_key=parent_key) for item in value]
        if parent_key == "image_content" and isinstance(value, str):
            return cls.OMITTED_IMAGE_CONTENT_TEMPLATE.format(length=len(value))
        if isinstance(value, str) and len(value) > cls.MAX_JSON_VALUE_LENGTH:
            trimmed_length = max(
                0,
                cls.MAX_JSON_VALUE_LENGTH - len(cls.TRUNCATED_SUFFIX),
            )
            return f"{value[:trimmed_length]}{cls.TRUNCATED_SUFFIX}"
        return value

    def save(self, *args, **kwargs):
        if not self.name:
            timestamp = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
            self.name = f"{self.tool_name} - {timestamp}"

        self.payload_content = self.sanitize_json_content(value=self.payload_content)
        self.response_content = self.sanitize_json_content(value=self.response_content)
        super().save(*args, **kwargs)


class AbstractAiProcess(models.Model):
    transaction = models.ForeignKey('billing.AiPointTransaction', on_delete=models.CASCADE)
    prompt = models.TextField()
    result = models.TextField()
    result_time = models.FloatField()
    input_tokens = models.FloatField(null=True, blank=True)
    output_tokens = models.FloatField(null=True, blank=True)
    cached_tokens = models.FloatField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=8)

    class Meta:
        abstract = True


class AiGenerateProcess(AbstractAiProcess):
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Content Generation for {self.product} - Cost: {self.cost}"


class AiTranslationProcess(AbstractAiProcess):
    to_translate = models.TextField()
    from_language_code = models.CharField(max_length=10)
    to_language_code = models.CharField(max_length=10)

    def __str__(self):
        return f"Translation from {self.from_language_code} to {self.to_language_code} - Cost: {self.cost}"


class AiImportProcess(AbstractAiProcess):
    PROPERTY_TYPE_DETECTOR = 'PROPERTY_TYPE_DETECTOR'
    IMPORTABLE_PROPERTIES_DETECTOR = 'IMPORTABLE_PROPERTIES_DETECTOR'

    TYPE_CHOICES = (
        (PROPERTY_TYPE_DETECTOR, 'Property Type Detector'),
        (IMPORTABLE_PROPERTIES_DETECTOR, 'Detects Importable Properties'),
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=PROPERTY_TYPE_DETECTOR,
        help_text="Type of AI import process."
    )

    def __str__(self):
        return f"Import Process ({self.get_type_display()}) - Cost: {self.cost}"


class BrandCustomPrompt(models.Model):
    LANGUAGES = get_languages()

    brand_value = models.ForeignKey('properties.PropertySelectValue', on_delete=models.CASCADE)
    language = models.CharField(max_length=LANGUAGE_MAX_LENGTH, choices=LANGUAGES, default=settings.LANGUAGE_CODE, null=True, blank=True)
    prompt = models.TextField()


    class Meta:
        unique_together = ('brand_value', 'language')

    def save(self, *args, **kwargs):
        if self.brand_value.property.internal_name != 'brand':
            raise ValidationError("Brand value must belong to property with internal_name 'brand'")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand_value.value} - {self.language or 'any'}"


class ChatGptProductFeedConfig(models.Model):
    REQUIRED_ON_UPDATE_FIELDS = (
        "condition_property",
        "brand_property",
        "material_property",
        "color_property",
        "size_property",
    )

    PROPERTY_VALUE_FIELDS = {
        "condition_property": (
            "condtion_new_value",
            "condtion_refurbished_value",
            "condtion_usd_value",
        ),
        "age_group_property": (
            "age_group_newborn_value",
            "age_group_infant_value",
            "age_group_todler_value",
            "age_group_kids_value",
            "age_group_adult_value",
        ),
        "pickup_method_property": (
            "pickup_method_in_store_value",
            "pickup_method_reserve_value",
            "pickup_method_not_supported_value",
        ),
        "gender_property": (
            "gender_male_value",
            "gender_female_value",
            "gender_unisex_value",
        ),
    }

    condition_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    brand_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    material_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    mpn_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    length_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    length_unit = models.CharField(
        max_length=32,
        blank=True,
    )
    width_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    height_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    weight_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    weight_unit = models.CharField(
        max_length=32,
        blank=True,
    )
    age_group_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    condtion_new_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    condtion_refurbished_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    condtion_usd_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_group_newborn_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_group_infant_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_group_todler_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_group_kids_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_group_adult_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    expiration_date_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    pickup_method_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    pickup_method_in_store_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    pickup_method_reserve_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    pickup_method_not_supported_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    color_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    size_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    size_system_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    gender_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    gender_male_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    gender_female_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    gender_unisex_value = models.ForeignKey(
        "properties.PropertySelectValue",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    popularity_score_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    warning_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    age_restriction_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    def clean(self):
        super().clean()

        errors = {}

        if self.pk:
            for field_name in self.REQUIRED_ON_UPDATE_FIELDS:
                if getattr(self, field_name) is None:
                    errors[field_name] = ValidationError(_("This field is required."))

        for property_field, value_fields in self.PROPERTY_VALUE_FIELDS.items():
            property_instance = getattr(self, property_field)
            for value_field in value_fields:
                value_instance = getattr(self, value_field)
                if value_instance is None:
                    continue
                if property_instance is None:
                    errors[value_field] = ValidationError(
                        _("A matching property must be set before assigning this value.")
                    )
                    continue
                if value_instance.property_id != property_instance.id:
                    errors[value_field] = ValidationError(
                        _("This value does not belong to the configured property.")
                    )

        if errors:
            raise ValidationError(errors)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["multi_tenant_company"],
                name="unique_chatgpt_product_feed_config_per_company",
            )
        ]
