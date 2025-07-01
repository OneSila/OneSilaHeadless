from core import models
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel


class RemoteProperty(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Model representing the remote mirror of a local Property.
    This model tracks the remote property associated with a local Property.
    """
    local_instance = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True,
                                       help_text="The local property associated with this remote property.")

    allow_multiple = models.BooleanField(
        default=False,
        help_text=(
            "Set to True to allow multiple remote properties to map "
            "to the same local property."
        ),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("sales_channel", "local_instance"),
                condition=models.Q(allow_multiple=False),
                name="uniq_remoteproperty_by_channel_local_when_not_multi",
            )
        ]
        verbose_name = 'Remote Property'
        verbose_name_plural = 'Remote Properties'

    def __str__(self):
        try:
            return f"Remote property for {self.local_instance.internal_name} on {self.sales_channel.hostname}"
        except AttributeError:
            return self.safe_str


class RemotePropertySelectValue(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a PropertySelectValue.
    """
    local_instance = models.ForeignKey('properties.PropertySelectValue',
                                       on_delete=models.SET_NULL,
                                       null=True,
                                       help_text="The local PropertySelectValue associated with this remote value.")
    remote_property = models.ForeignKey(RemoteProperty, on_delete=models.CASCADE, help_text="The remote property associated with this remote value.")

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Property Select Value'
        verbose_name_plural = 'Remote Property Select Values'

    def __str__(self):
        local_value = self.local_instance.value if self.local_instance else "N/A"
        sales_channel = self.sales_channel.hostname if hasattr(self, 'sales_channel') and self.sales_channel else "N/A"
        return f"Remote value for {local_value} on {sales_channel}"


class RemoteProductProperty(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a ProductProperty.
    """
    local_instance = models.ForeignKey('properties.ProductProperty', on_delete=models.SET_NULL, null=True,
                                       help_text="The local ProductProperty instance associated with this remote property.")
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this property.")
    remote_property = models.ForeignKey('sales_channels.RemoteProperty', on_delete=models.CASCADE, null=True,
                                        help_text="The remote property associated with this product property.")
    remote_value = models.TextField(null=True, blank=True, help_text="The value of this property in the remote system, stored as a string.")

    class Meta:
        unique_together = ('remote_product', 'local_instance')
        verbose_name = 'Remote Product Property'
        verbose_name_plural = 'Remote Product Properties'

    @property
    def frontend_name(self):
        return f"{self.local_instance.property.name} > {self.local_instance.get_value()}"

    def __str__(self):
        if self.local_instance:
            property_name = self.local_instance.property.internal_name
            property_value = self.local_instance.get_value()
        else:
            property_name = "No Property"
            property_value = "No Value"

        return f"{self.remote_product} {property_name} > {property_value}"

    def needs_update(self, new_remote_value):
        """
        Checks if the remote value differs from the new value that is intended to be updated.
        Converts both values to string for comparison to handle various data types uniformly.

        :param new_remote_value: The new value intended to be set in the remote system.
        :return: Boolean indicating whether an update is needed.
        """
        # Convert new_remote_value to string for comparison
        new_value_str = str(new_remote_value)

        # Compare the new value with the current remote_value
        return new_value_str != self.remote_value
