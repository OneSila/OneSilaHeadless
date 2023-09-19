from core import models


class Unit(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=5)

    def __str__(self):
        return self.unit
