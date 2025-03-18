from core import models


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