from core import models
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel

class RemoteVat(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a VAT rate.
    """

    local_instance = models.ForeignKey('taxes.VatRate', on_delete=models.SET_NULL, null=True, help_text="The local VAT rate instance associated with this remote VAT.")

    class Meta:
        unique_together = ('local_instance',)
        verbose_name = 'Remote VAT'
        verbose_name_plural = 'Remote VATs'

    def __str__(self):
        return f"Remote VAT for {self.local_instance.name} ({self.local_instance.rate}%)"

class RemoteCurrency(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a currency.
    """

    local_instance = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True, help_text="The local currency instance associated with this remote currency.")
    remote_code = models.CharField(
        max_length=10,
        help_text="The currency code in the remote system."
    )

    class Meta:
        unique_together = ('local_instance', 'sales_channel')
        verbose_name = 'Remote Currency'
        verbose_name_plural = 'Remote Currencies'

    def __str__(self):
        return f"{self.remote_code} @ {self.sales_channel.hostname}"