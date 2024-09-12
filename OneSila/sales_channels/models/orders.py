from core import models
from polymorphic.models import PolymorphicModel
from .mixins import RemoteObjectMixin

class RemoteOrder(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an Order.
    This model tracks the synchronization status and data for remote orders.
    """

    local_instance = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, help_text="The local order associated with this remote order.")
    raw_data = models.JSONField(help_text="Raw data from the remote system for this order.", null=True, blank=True)

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Order'
        verbose_name_plural = 'Remote Orders'

    def __str__(self):
        try:
            return f"Remote order for {self.local_instance.reference} on {self.sales_channel.hostname}"
        except AttributeError:
            return f"Remote order with remote ID {self.remote_id} on {self.sales_channel.hostname}"


class RemoteOrderItem(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an Order Item.
    This model tracks the synchronization status and data for remote order items.
    """

    local_instance = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        help_text="The local order item associated with this remote order item."
    )
    remote_order = models.ForeignKey(
        RemoteOrder,
        on_delete=models.CASCADE,
        help_text="The remote order to which this item belongs."
    )
    remote_product = models.ForeignKey(
        'sales_channels.RemoteProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The remote product associated with this order item."
    )
    price = models.FloatField(help_text="Price of the item in the remote order.")
    quantity = models.IntegerField(help_text="Quantity of the item in the remote order.")
    remote_sku = models.CharField(max_length=255, help_text="The SKU of the remote product in the moment it was pulled.")
    raw_data = models.JSONField(help_text="Raw data from the remote system for this customer.", null=True, blank=True)

    class Meta:
        unique_together = ('remote_order', 'local_instance')
        verbose_name = 'Remote Order Item'
        verbose_name_plural = 'Remote Order Items'

    def __str__(self):
        local_order_reference = self.remote_order.local_instance.reference if self.remote_order.local_instance else 'N/A'
        return f"Remote order item for order {local_order_reference} on {self.remote_order.sales_channel.hostname}"

class RemoteCustomer(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Customer.
    This model tracks the synchronization status and data for remote customers.
    """

    local_instance = models.ForeignKey('contacts.Customer', on_delete=models.SET_NULL, null=True, help_text="The local customer associated with this remote customer.")
    shipping_address = models.ForeignKey(
        'contacts.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remote_customers_shipping',
        help_text="The shipping address for this remote customer."
    )
    invoice_address = models.ForeignKey(
        'contacts.InvoiceAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remote_customers_invoice',
        help_text="The invoice address for this remote customer."
    )
    raw_data = models.JSONField(help_text="Raw data from the remote system for this customer.", null=True, blank=True)

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Customer'
        verbose_name_plural = 'Remote Customers'

    def __str__(self):
        return f"Remote customer for {self.local_instance.name} on {self.sales_channel.hostname}"
