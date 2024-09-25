from model_bakery.recipe import related

from core import models
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel

from ..signals import sync_remote_product


class RemoteProduct(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Product.
    """

    local_instance = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, db_index=True, help_text="The local Product instance associated with this remote product.")
    remote_sku = models.CharField(max_length=255, help_text="The SKU of the product in the remote system.")
    is_variation = models.BooleanField(default=False, help_text="Indicates if this product is a variation.")
    remote_parent_product = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, help_text="The remote parent product for variations.")

    # user wants last error
    # admin wants all the errors
    # in frontend show only the user errors. If the errors are admin we show a generic message but still let them resync so it maybe fixed

    class Meta:
        unique_together = (('sales_channel', 'local_instance', 'remote_parent_product'), ('sales_channel', 'remote_sku'),)
        verbose_name = 'Remote Product'
        verbose_name_plural = 'Remote Products'

    def __str__(self):
        return f"{self.local_instance.name} (SKU: {self.remote_sku})"


class RemoteInventory(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's inventory.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct', related_name='inventory', on_delete=models.CASCADE, help_text="The remote product associated with this inventory.")
    quantity = models.IntegerField(help_text="The quantity of the product available in the remote system.", null=True, blank=True)

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Inventory'
        verbose_name_plural = 'Remote Inventories'

    def __str__(self):
        return f"Inventory for {self.remote_product.local_instance.name} - Quantity: {self.quantity}"


class RemotePrice(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's price.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct',related_name='price', on_delete=models.CASCADE, help_text="The remote product associated with this price.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="The price of the product in the remote system.", null=True, blank=True,) # null for configurable products
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="The discounted price of the product in the remote system, if any.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Price'
        verbose_name_plural = 'Remote Prices'

    def __str__(self):
        return f"Price for {self.remote_product.local_instance.name} - {self.price}"


class RemoteProductContent(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the synchronization state of a product's content with a remote system.
    """

    remote_product = models.OneToOneField('sales_channels.RemoteProduct', related_name='content', on_delete=models.CASCADE, help_text="The remote product associated with this content.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Product Content'
        verbose_name_plural = 'Remote Product Contents'

    def __str__(self):
        return f"Content sync status for {self.remote_product.local_instance.name}"


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

    remote_properties = models.ManyToManyField(
        'sales_channels.RemoteProperty',
        related_name='configurators',
        help_text="The remote properties associated with this configurator."
    )

    objects = RemoteProductConfiguratorManager()

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Product Configurator'
        verbose_name_plural = 'Remote Product Configurators'

    def __str__(self):
        return f"Configurator for {self.remote_product.local_instance.name}"

    @classmethod
    def _get_all_remote_properties(cls, local_product, sales_channel, rule=None, variations=None):
        """
        Helper method to get all remote properties needed for the configurator.
        Returns a list of RemoteProperty instances.
        """
        from properties.models import ProductPropertiesRuleItem, ProductProperty
        from sales_channels.models import RemoteProperty
        from django.db.models import Count

        # Get the product rule if not provided
        if rule is None:
            rule = local_product.get_product_rule()

        if rule is None:
            raise ValueError(f"No product properties rule found for {local_product.name}")

        # Get required and optional properties for configurator
        configurator_properties = local_product.get_configurator_properties(product_rule=rule)

        # Separate required and optional in-configurator properties
        required_props_ids = configurator_properties.filter(
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
        ).values_list('property_id', flat=True)

        optional_props_ids = configurator_properties.filter(
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
        ).values_list('property_id', flat=True)

        # Fetch RemoteProperty instances for required properties
        remote_required_props = list(RemoteProperty.objects.filter(
            local_instance_id__in=required_props_ids,
            sales_channel=sales_channel
        ))

        # For optional properties, check if variations have different values
        remote_optional_props = []
        if optional_props_ids:
            if variations is None:
                # Fetch variations if not provided
                variations = local_product.get_configurable_variations(active_only=True)

            variation_ids = variations.values_list('id', flat=True)

            # Fetch property values for variations
            prop_values = ProductProperty.objects.filter(
                product_id__in=variation_ids,
                property_id__in=optional_props_ids
            ).values('property_id').annotate(
                distinct_values=Count('value_select', distinct=True)
            )

            # Include properties where the count of distinct values is greater than 1
            varying_props_ids = [
                pv['property_id'] for pv in prop_values if pv['distinct_values'] > 1
            ]

            # Fetch RemoteProperty instances for these varying optional properties
            if varying_props_ids:
                remote_optional_props = list(RemoteProperty.objects.filter(
                    local_instance_id__in=varying_props_ids,
                    sales_channel=sales_channel
                ))

        # Combine required and optional RemoteProperties
        all_remote_props = remote_required_props + remote_optional_props

        return all_remote_props

    def update_if_needed(self, rule=None, variations=None, send_sync_signal=True):
        """
        Updates the remote_properties if there are changes based on the current rule and variations.
        """
        local_product = self.remote_product.local_instance
        sales_channel = self.remote_product.sales_channel

        # Use the helper method to get all remote properties
        all_remote_props = self._get_all_remote_properties(
            local_product, sales_channel, rule=rule, variations=variations
        )

        # Update the configurator's remote_properties if needed
        existing_remote_props_ids = set(self.remote_properties.values_list('id', flat=True))
        new_remote_props_ids = set(rp.id for rp in all_remote_props)

        if existing_remote_props_ids != new_remote_props_ids:
            self.remote_properties.set(all_remote_props)
            self.save()

            if send_sync_signal:
                sync_remote_product.send(sender=self.remote_product.local_instance.__class__, instance=self.remote_product.local_instance.product)


class RemoteImage(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an image in the media library.
    """
    local_instance = models.ForeignKey('media.Media', on_delete=models.SET_NULL, null=True, help_text="The local media instance associated with this remote image.")

    class Meta:
        unique_together = ('local_instance', 'sales_channel',)
        verbose_name = 'Remote Image'
        verbose_name_plural = 'Remote Images'

    def __str__(self):
        return f"Remote image for {self.local_instance}"


class RemoteImageProductAssociation(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the association of a remote image with a remote product.
    """
    local_instance = models.ForeignKey('media.MediaProductThrough', on_delete=models.SET_NULL, null=True, help_text="The local MediaProductThrough instance associated with this remote association.")
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this image assignment.")
    remote_image = models.ForeignKey(RemoteImage, on_delete=models.CASCADE, null=True, blank=True, help_text="The remote image being assigned to the remote product. Optional for direct links.")

    class Meta:
        unique_together = ('local_instance', 'sales_channel', 'remote_product',)
        verbose_name = 'Remote Image Product Association'
        verbose_name_plural = 'Remote Image Product Associations'

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