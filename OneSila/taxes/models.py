from core import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class VatRate(models.Model):
    """
    Tax value class to assign taxes to products. These are not to be confused
    with the international rates one should charge (e.g., in the Euro-zone).

    At least one of 'name' or 'rate' must be provided.
    """
    name = models.CharField(max_length=20, null=True, blank=True)
    rate = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("VAT rate in percent. Eg 21 for 21%")
    )

    def clean(self):
        if not self.name and self.rate is None:
            raise ValidationError(_("Either 'name' or 'rate' must be provided."))

    def __str__(self):
        return f"{self.name or 'Unnamed'} ({self.rate if self.rate is not None else 'No rate'}%) @ {self.multi_tenant_company}"

    class Meta:
        verbose_name = 'VAT Rate'
        verbose_name_plural = 'VAT Taxes'
