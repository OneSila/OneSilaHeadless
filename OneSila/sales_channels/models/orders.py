from core import models
from polymorphic.models import PolymorphicModel
from .mixins import RemoteObjectMixin

class RemoteOrder(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an Order.
    This model tracks the synchronization status and data for remote orders.
    """

    local_instance = models.ForeignKey('orders.Order', on_delete=models.CASCADE, help_text="The local order associated with this remote order.")
    raw_data = models.JSONField(help_text="Raw data from the remote system for this order.", null=True, blank=True)

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Order'
        verbose_name_plural = 'Remote Orders'

    def __str__(self):
        return f"Remote order for {self.local_instance.reference} on {self.sales_channel.hostname}"


class RemoteCustomer(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Customer.
    This model tracks the synchronization status and data for remote customers.
    """

    local_instance = models.ForeignKey('contacts.Customer', on_delete=models.CASCADE, help_text="The local customer associated with this remote customer.")
    shipping_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.SET_NULL, null=True, blank=True, help_text="The shipping address for this remote customer.")
    invoice_address = models.ForeignKey('contacts.InvoiceAddress', on_delete=models.SET_NULL, null=True, blank=True, help_text="The invoice address for this remote customer.")
    raw_data = models.JSONField(help_text="Raw data from the remote system for this customer.", null=True, blank=True)

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Customer'
        verbose_name_plural = 'Remote Customers'

    def __str__(self):
        return f"Remote customer for {self.local_instance.name} on {self.sales_channel.hostname}"
