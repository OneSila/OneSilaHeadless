from django.conf import settings
from core import models
from core.helpers import get_languages
from django.core.exceptions import ValidationError


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
