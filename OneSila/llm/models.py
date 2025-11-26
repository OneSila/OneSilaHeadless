from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core import models
from core.helpers import get_languages


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
    language = models.CharField(max_length=7, choices=LANGUAGES, default=settings.LANGUAGE_CODE, null=True, blank=True)
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
