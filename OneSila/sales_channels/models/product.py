from core import models
from .mixins import RemoteObjectMixin
from polymorphic.models import PolymorphicModel

class RemoteProduct(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Product.
    """

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True, help_text="The local Product instance associated with this remote product.")
    remote_sku = models.CharField(max_length=255, help_text="The SKU of the product in the remote system.")
    is_variation = models.BooleanField(default=False, help_text="Indicates if this product is a variation.")
    remote_parent_product = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, help_text="The remote parent product for variations.")
    payload = models.JSONField(help_text="The JSON payload representing this product in the remote system.")
    utdated = models.BooleanField(default=False, help_text="Indicates if the remote product is outdated due to an error.")
    outdated_since = models.DateTimeField(null=True, blank=True, help_text="The timestamp when this remote product became outdated.")

    class Meta:
        unique_together = ('sales_channel', 'product')
        verbose_name = 'Remote Product'
        verbose_name_plural = 'Remote Products'

    def __str__(self):
        return f"{self.product.name} (SKU: {self.remote_sku})"

    def need_update(self, new_payload):
        import json
        """
        Compares the current payload with a new one to determine if an update is needed.
        """
        return json.dumps(self.payload, sort_keys=True) != json.dumps(new_payload, sort_keys=True)

    def mark_outdated(self, save=True):
        """
        Marks the assign as outdated due to an error and sets the outdated_since timestamp.
        """
        self.outdated = True
        self.outdated_since = models.DateTimeField(auto_now=True)
        if save:
            self.save()

    def get_related_error_logs(self):
        """
        Retrieves all related error logs through the associated RemoteProduct and filters by outdated_since.
        """
        if not self.outdated_since:
            return None

        # @TODO: Extend that to also use errors from stock, price,e product properties error and so on
        return self.remotelog_set.filter(
            status=RemoteLog.STATUS_FAILED,
            created_at__gte=self.outdated_since
        )

class RemoteInventory(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's inventory.
    """

    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this inventory.")
    quantity = models.IntegerField(help_text="The quantity of the product available in the remote system.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Inventory'
        verbose_name_plural = 'Remote Inventories'

    def __str__(self):
        return f"Inventory for {self.remote_product.product.name} - Quantity: {self.quantity}"

class RemotePrice(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a product's price.
    """

    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this price.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="The price of the product in the remote system.")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="The discounted price of the product in the remote system, if any.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Price'
        verbose_name_plural = 'Remote Prices'

    def __str__(self):
        return f"Price for {self.remote_product.product.name} - {self.price}"

class RemoteProductContent(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the synchronization state of a product's content with a remote system.
    """

    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this content.")

    class Meta:
        unique_together = ('remote_product',)
        verbose_name = 'Remote Product Content'
        verbose_name_plural = 'Remote Product Contents'

    def __str__(self):
        return f"Content sync status for {self.remote_product.product.name}"

class RemoteImage(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of an image in the media library.
    """
    local_instance = models.ForeignKey('media.Media', on_delete=models.CASCADE, help_text="The local media instance associated with this remote image.")

    class Meta:
        unique_together = ('local_instance',)
        verbose_name = 'Remote Image'
        verbose_name_plural = 'Remote Images'

    def __str__(self):
        return f"Remote image for {self.local_instance}"


class RemoteImageProductAssociation(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the association of a remote image with a remote product.
    """
    local_instance = models.ForeignKey('MediaProductThrough', on_delete=models.CASCADE, help_text="The local MediaProductThrough instance associated with this remote association.")
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.CASCADE, help_text="The remote product associated with this image assignment.")
    remote_image = models.ForeignKey('sales_channels.RemoteImage', on_delete=models.CASCADE, help_text="The remote image being assigned to the remote product.")

    class Meta:
        unique_together = ('remote_product', 'remote_image')
        verbose_name = 'Remote Image Product Association'
        verbose_name_plural = 'Remote Image Product Associations'

    def __str__(self):
        return f"{self.remote_image} associated with {self.remote_product.product.name}"


class RemoteCategory(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a category.
    This is a placeholder for future implementation.
    """
    pass

    class Meta:
        verbose_name = 'Remote Category'
        verbose_name_plural = 'Remote Categories'