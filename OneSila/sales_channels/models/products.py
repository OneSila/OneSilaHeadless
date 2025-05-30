from django.db.models import UniqueConstraint, Q
from model_bakery.recipe import related

from core import models
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel
from django.core.validators import MinValueValidator, MaxValueValidator
from ..signals import sync_remote_product
from django.utils.translation import gettext_lazy as _


class RemoteProduct(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Product.
    """

    local_instance = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, db_index=True,
                                       help_text="The local Product instance associated with this remote product.")
    remote_sku = models.CharField(max_length=255, help_text="The SKU of the product in the remote system.", null=True, blank=True)
    is_variation = models.BooleanField(default=False, help_text="Indicates if this product is a variation.")
    remote_parent_product = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, help_text="The remote parent product for variations.")
    syncing_current_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Current sync progress percentage (0-100)."
    )

    class Meta:
        unique_together = (('sales_channel', 'local_instance', 'remote_parent_product'),)
        constraints = [
            UniqueConstraint(
                fields=['sales_channel', 'remote_sku'],
                condition=Q(remote_sku__isnull=False),
                name='unique_remote_sku_per_channel_if_present'
            ),
        ]
        verbose_name = 'Remote Product'
        verbose_name_plural = 'Remote Products'

    def set_new_sync_percentage(self, new_percentage: int):
        """
        Sets a new sync progress percentage for the remote product.

        :param new_percentage: An integer value between 0 and 100.
        :raises ValueError: If new_percentage is not in the valid range.
        """
        if not (0 <= new_percentage <= 100):
            raise ValueError("Sync percentage must be between 0 and 100.")

        self.syncing_current_percentage = new_percentage
        self.save(update_fields=['syncing_current_percentage'])

    @property
    def frontend_name(self):
        return f"{self.local_instance.name} ({self.remote_sku})"

    @property
    def errors(self):
        from integrations.models import IntegrationLog

        if not self.pk:
            return IntegrationLog.objects.none()

        # Retrieve the latest logs grouped by identifier (using distinct on 'identifier')
        latest_logs = IntegrationLog.objects.filter(remote_product=self).order_by('identifier', '-created_at').distinct('identifier')

        # Now build a list of error IDs that should remain, i.e. where a more recent fix log is not present.
        error_ids = []
        for log in latest_logs:

            if log.status != IntegrationLog.STATUS_FAILED:
                continue

            # If a fixing_identifier is set on this log, check if a later successful log with that fixing_identifier exists.
            if log.fixing_identifier:
                fixed = IntegrationLog.objects.filter(remote_product=self,
                                                      identifier=log.fixing_identifier,
                                                      status=IntegrationLog.STATUS_SUCCESS,
                                                      created_at__gt=log.created_at).exists()

                if fixed:
                    continue

            error_ids.append(log.id)

        return IntegrationLog.objects.filter(id__in=error_ids)

    def __str__(self):
        local_name = self.local_instance.name if self.local_instance else "N/A"
        remote_sku = self.remote_sku if self.remote_sku else "N/A"
        sales_channel = self.sales_channel.hostname if hasattr(self, 'sales_channel') and self.sales_channel else "N/A"
        return f"Remote product {local_name} (SKU: {remote_sku}) on {sales_channel}"


class RemoteInventory(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's inventory.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct', related_name='inventory',
                                          on_delete=models.CASCADE, help_text="The remote product associated with this inventory.")
    quantity = models.IntegerField(help_text="The quantity of the product available in the remote system.", null=True, blank=True)

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Inventory'
        verbose_name_plural = 'Remote Inventories'

    def __str__(self):
        return f"Inventory for {self.remote_product} - Quantity: {self.quantity}"


class RemotePrice(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's price.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct', related_name='price', on_delete=models.CASCADE,
                                          help_text="The remote product associated with this price.")
    price_data = models.JSONField(default=dict, blank=True, help_text="Multi-currency price and discount data.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Price'
        verbose_name_plural = 'Remote Prices'

    def __str__(self):
        return f"Price for {self.remote_product} - {self.frontend_name}"

    def get_price_for_currency(self, currency_code):
        return self.price_data.get(currency_code, {})

    @property
    def frontend_name(self):

        if not self.price_data:
            return "No prices"

        parts = []
        for currency_code, values in self.price_data.items():
            price = values.get("price")
            discount = values.get("discount_price")
            if discount is not None:
                parts.append(f"{currency_code}: {price} → {discount}")
            else:
                parts.append(f"{currency_code}: {price}")

        return " | ".join(parts)


class RemoteProductContent(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the synchronization state of a product's content with a remote system.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct', related_name='content', on_delete=models.CASCADE,
                                          help_text="The remote product associated with this content.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Product Content'
        verbose_name_plural = 'Remote Product Contents'

    def __str__(self):
        return f"Content sync status for {self.remote_product}"

    @property
    def frontend_name(self):
        return (_(f"Content for {self.remote_product.local_instance.name}"))


class RemoteProductConfigurator(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the configuration of remote products, managing the required and optional properties
    based on the configuration rules for product variations.
    """
    from ..managers import RemoteProductConfiguratorManager

    remote_product = models.OneToOneField(
        'sales_channels.RemoteProduct',
        on_delete=models.CASCADE,
        related_name='configurator',
        help_text="The remote product associated with this configurator."
    )

    properties = models.ManyToManyField(
        'properties.Property',
        related_name='configurators',
        help_text="Local properties used for configurator logic."
    )

    objects = RemoteProductConfiguratorManager()

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Product Configurator'
        verbose_name_plural = 'Remote Product Configurators'

    @property
    def frontend_name(self):
        return (_(f"Configurator for {self.remote_product.local_instance.name}"))

    @property
    def remote_properties(self):
        from sales_channels.models import RemoteProperty

        return RemoteProperty.objects.filter(
            local_instance__in=self.properties.all(),
            sales_channel=self.remote_product.sales_channel
        )

    def __str__(self):
        return f"Configurator for {self.remote_product}"

    @classmethod
    def _get_all_properties(cls, local_product, sales_channel, rule=None, variations=None):
        """
        Helper method to get all local properties (Property instances) needed for the configurator.
        These are properties that must be mirrored to remote channels.
        """
        from properties.models import ProductPropertiesRuleItem, ProductProperty, Property
        from django.db.models import Count

        if rule is None:
            rule = local_product.get_product_rule()

        if rule is None:
            raise ValueError(f"No product properties rule found for {local_product.name}")

        configurator_properties = local_product.get_configurator_properties(product_rule=rule)

        required_ids = configurator_properties.filter(
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
        ).values_list('property_id', flat=True)

        optional_ids = configurator_properties.filter(
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
        ).values_list('property_id', flat=True)

        # For optional properties, determine which vary
        varying_optional_ids = []
        if optional_ids:
            if variations is None:
                variations = local_product.get_configurable_variations(active_only=True)

            variation_ids = variations.values_list('id', flat=True)

            prop_values = ProductProperty.objects.filter(
                product_id__in=variation_ids,
                property_id__in=optional_ids
            ).values('property_id').annotate(
                distinct_values=Count('value_select', distinct=True)
            )

            varying_optional_ids = [
                pv['property_id'] for pv in prop_values if pv['distinct_values'] > 1
            ]

        all_ids = list(required_ids) + varying_optional_ids

        return list(Property.objects.filter(id__in=all_ids))

    def update_if_needed(self, rule=None, variations=None, send_sync_signal=True):
        """
        Updates the `properties` (local Property instances) if there are changes based on the current rule and variations.
        """
        local_product = self.remote_product.local_instance
        sales_channel = self.remote_product.sales_channel

        all_props = self._get_all_properties(
            local_product,
            sales_channel,
            rule=rule,
            variations=variations
        )

        existing_prop_ids = set(self.properties.values_list('id', flat=True))
        new_prop_ids = set(p.id for p in all_props)

        if existing_prop_ids != new_prop_ids:
            self.properties.set(all_props)
            self.save()

            if send_sync_signal:
                sync_remote_product.send(
                    sender=self.remote_product.local_instance.__class__,
                    instance=self.remote_product.local_instance.product
                )


class RemoteImage(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an image in the media library.
    """
    local_instance = models.ForeignKey('media.Media', on_delete=models.SET_NULL, null=True,
                                       help_text="The local media instance associated with this remote image.")

    class Meta:
        unique_together = ('local_instance', 'sales_channel',)
        verbose_name = 'Remote Image'
        verbose_name_plural = 'Remote Images'

    @property
    def frontend_name(self):
        return (_(f"Image for {self.remote_product.local_instance.name}"))

    def __str__(self):
        return f"Remote image for {self.local_instance}"


class RemoteImageProductAssociation(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the association of a remote image with a remote product.
    """
    local_instance = models.ForeignKey('media.MediaProductThrough', on_delete=models.SET_NULL, null=True,
                                       help_text="The local MediaProductThrough instance associated with this remote association.")
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE,
                                       help_text="The remote product associated with this image assignment.")
    remote_image = models.ForeignKey(RemoteImage, on_delete=models.CASCADE, null=True, blank=True,
                                     help_text="The remote image being assigned to the remote product. Optional for direct links.")

    class Meta:
        unique_together = ('local_instance', 'sales_channel', 'remote_product',)
        verbose_name = 'Remote Image Product Association'
        verbose_name_plural = 'Remote Image Product Associations'

    @property
    def frontend_name(self):
        return (_(f"Image for {self.remote_product.local_instance.name}"))

    def __str__(self):
        local_product_name = self.local_instance.product.name if self.local_instance and self.local_instance.product else "No Local Product"
        remote_image_desc = str(self.remote_image) if self.remote_image else "No Remote Image"
        return f"{remote_image_desc} associated with {local_product_name}"


class RemoteCategory(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a category.
    This is a placeholder for future implementation.
    """
    pass

    class Meta:
        verbose_name = 'Remote Category'
        verbose_name_plural = 'Remote Categories'


class RemoteEanCode(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Remote mirror model for an EAN code.
    Stores the EAN code value directly and associates it with a remote product on Magento.
    """
    ean_code = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        help_text="The EAN code value."
    )
    remote_product = models.ForeignKey(
        'sales_channels.RemoteProduct',
        related_name='eancode',
        on_delete=models.CASCADE,
        help_text="The remote product associated with this EAN code."
    )

    class Meta:
        unique_together = ('ean_code', 'remote_product')
        verbose_name = 'Remote EAN Code'
        verbose_name_plural = 'Remote EAN Codes'

    @property
    def frontend_name(self):

        if self.ean_code is None:
            return "N/A"

        return self.ean_code

    def __str__(self):
        sales_channel = (
            self.remote_product.sales_channel.hostname
            if hasattr(self.remote_product, 'sales_channel') and self.remote_product.sales_channel
            else "N/A"
        )
        return f"Remote EAN Code {self.ean_code or 'N/A'} for {sales_channel}"
