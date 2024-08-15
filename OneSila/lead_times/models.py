from core import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from contacts.models import ShippingAddress, InventoryShippingAddress
from .managers import LeadTimeManager
from products.models import Product
from products.product_types import MANUFACTURABLE, SUPPLIER


class LeadTime(models.Model):
    HOUR = 1
    DAY = 2
    WEEK = 3
    MONTH = 4

    UNIT_CHOICES = (
        (HOUR, _('Hour')),
        (DAY, _('Day')),
        (WEEK, _('Week')),
        (MONTH, _('Month')),
    )

    min_time = models.IntegerField()
    max_time = models.IntegerField()
    unit = models.IntegerField(choices=UNIT_CHOICES)
    shippingaddresses = models.ManyToManyField(
        ShippingAddress,
        blank=True,
        through='LeadTimeForShippingAddress',
        symmetrical=False,
        related_name='leadtimes'
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        through='LeadTimeProductOutOfStock',
        symmetrical=False,
        related_name='leadtimes_outofstock'
    )

    objects = LeadTimeManager()

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"{self.min_time} - {self.max_time} {self.get_unit_display()}(s)"

    class Meta:
        search_terms = []
        unique_together = ['multi_tenant_company', 'min_time', 'max_time', 'unit']
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_time__gte=models.F("min_time")),
                name=_("Maximum Time cannot be less then Minimum Time"),
            ),
            models.CheckConstraint(
                check=models.Q(max_time__gte=0),
                name=_("Maximum time cannot be 0"),
            ),
            models.CheckConstraint(
                check=models.Q(min_time__gte=0),
                name=_("Minimum Time cannot be 0"),
            ),
        ]


class LeadTimeForShippingAddress(models.Model):
    shippingaddress = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    leadtime = models.ForeignKey(LeadTime, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return f"{self.shippingaddress} <{self.leadtime.name}>"

    class Meta:
        unique_together = ['multi_tenant_company', 'shippingaddress']


class LeadTimeProductOutOfStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    leadtime_outofstock = models.ForeignKey(LeadTime, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return f"{self.product} <{self.leadtime.name}>"

    def save(self, *args, **kwargs):
        if self.product.type not in [MANUFACTURABLE, SUPPLIER]:
            raise ValidationError(_("Out of stock Leadtimes can only be set on Supplier and Manufacturable products."))

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['multi_tenant_company', 'product']
