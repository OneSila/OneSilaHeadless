from core import models


class AiGenerateProcess(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey('billing.AiPointTransaction', on_delete=models.CASCADE)
    prompt = models.TextField()
    result = models.TextField()
    result_time = models.FloatField()
    input_tokens = models.FloatField(null=True, blank=True)
    output_tokens = models.FloatField(null=True, blank=True)
    cached_tokens = models.FloatField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return f"Content Generation for {self.product} - Cost: {self.cost}"


class AiTranslationProcess(models.Model):
    to_translate = models.TextField()
    from_language_code = models.CharField(max_length=10)
    to_language_code = models.CharField(max_length=10)

    transaction = models.ForeignKey('billing.AiPointTransaction', on_delete=models.CASCADE)
    result = models.TextField()
    result_time = models.FloatField()
    input_tokens = models.FloatField(null=True, blank=True)
    output_tokens = models.FloatField(null=True, blank=True)
    cached_tokens = models.FloatField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=8)

    def __str__(self):
        return f"Translation from {self.from_language_code} to {self.to_language_code} - Cost: {self.cost}"