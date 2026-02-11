from core import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from properties.models import Property
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel
from sales_channels.constants import REMOTE_PROPERTY_TYPE_CHANGE_RULES


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
    original_type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        null=True,
        blank=True,
        help_text="Original remote property type before any manual remapping.",
    )
    type = models.CharField(
        max_length=16,
        choices=Property.TYPES.ALL,
        null=True,
        blank=True,
        help_text="Remote property type stored on the base RemoteProperty model.",
    )
    allows_unmapped_values = models.BooleanField(
        default=False,
        help_text="Whether this remote property accepts values outside predefined options.",
    )
    yes_text_value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Text value treated as True when mapping text-like remote values to boolean.",
    )
    no_text_value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Text value treated as False when mapping text-like remote values to boolean.",
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

    def _resolve_sales_channel_app_label(self):
        if not self.sales_channel_id:
            return None

        channel = self.sales_channel
        get_real_instance = getattr(channel, "get_real_instance", None)
        if callable(get_real_instance):
            channel = get_real_instance()

        return channel._meta.app_label

    def _resolve_original_type_key(self):
        if self.original_type == Property.TYPES.SELECT:
            return "SELECT__allows_custom_values" if self.allows_unmapped_values else "SELECT__not_allows_custom_values"
        if self.original_type == Property.TYPES.MULTISELECT:
            return "MULTISELECT__allows_custom_values" if self.allows_unmapped_values else "MULTISELECT__not_allows_custom_values"
        return self.original_type

    def _type_change_allowed(self, *, target_type):
        rule_key = self._resolve_original_type_key()
        allowed_targets = REMOTE_PROPERTY_TYPE_CHANGE_RULES.get(rule_key, {})
        return bool(allowed_targets.get(target_type))

    def save(self, *args, **kwargs):
        app_label = self._resolve_sales_channel_app_label()

        if app_label == "amazon" and self.allow_multiple is not True:
            self.allow_multiple = True

        if app_label in {"magento2", "woocommerce"} and self.local_instance and self.local_instance.type:
            self.original_type = self.local_instance.type
            self.type = self.local_instance.type

        if self.original_type and self.type is None:
            self.type = self.original_type

        if self.original_type is None and self.type:
            self.original_type = self.type

        if self.original_type and self.type and not self._type_change_allowed(target_type=self.type):
            raise ValidationError(
                _(
                    "Remote property original type %(original)s cannot be changed to %(target)s."
                )
                % {
                    "original": self.get_original_type_display(),
                    "target": self.get_type_display(),
                }
            )

        if self.local_instance and self.type and self.local_instance.type != self.type:
            raise ValidationError(
                _(
                    "Remote property type %(remote)s must match local property type %(local)s."
                )
                % {
                    "remote": self.get_type_display(),
                    "local": self.local_instance.get_type_display(),
                }
            )

        super().save(*args, **kwargs)


class RemotePropertySelectValue(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a PropertySelectValue.
    """
    local_instance = models.ForeignKey('properties.PropertySelectValue',
                                       on_delete=models.SET_NULL,
                                       null=True,
                                       blank=True,
                                       help_text="The local PropertySelectValue associated with this remote value.")
    remote_property = models.ForeignKey(RemoteProperty, on_delete=models.CASCADE, help_text="The remote property associated with this remote value.")
    bool_value = models.BooleanField(
        null=True,
        blank=True,
        help_text="Boolean meaning for this option when mapping select/multiselect remote values to boolean.",
    )

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
