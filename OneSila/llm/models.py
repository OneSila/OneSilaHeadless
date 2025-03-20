from core import models

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
    TYPE_CHOICES = (
        (PROPERTY_TYPE_DETECTOR, 'Property Type Detector'),
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=PROPERTY_TYPE_DETECTOR,
        help_text="Type of AI import process."
    )

    def __str__(self):
        return f"Import Process ({self.get_type_display()}) - Cost: {self.cost}"