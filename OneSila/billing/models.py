from core import models
from .managers import AiPointContentGenerateProcessManager


class AiPointTransaction(models.Model):
    ADD = 'ADD'
    SUBTRACT = 'SUBTRACT'

    TRANSACTION_TYPE_CHOICES = [
        (ADD, 'Adding'),
        (SUBTRACT, 'Subtracting'),
    ]
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)

    def __str__(self):
        return f"{self.multi_tenant_company} > {self.transaction_type} {self.points} points"

class AiPointContentGenerateProcess(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(AiPointTransaction, on_delete=models.CASCADE)
    prompt = models.TextField()
    result = models.TextField()
    result_time = models.FloatField()
    cost = models.DecimalField(max_digits=10, decimal_places=4)

    objects = AiPointContentGenerateProcessManager()

    def __str__(self):
        return f"Content Generation for {self.product} - Cost: {self.cost}"