from core import models
from polymorphic.models import PolymorphicModel

from imports_exports.models import Import, ImportableModel
from sales_channels.models.sales_channels import SalesChannel
from .products import (
    RemoteProduct,
    RemoteImage,
)
from .properties import RemoteProperty, RemotePropertySelectValue
from .taxes import RemoteVat, RemoteCurrency

class SalesChannelImport(Import, models.Model):
    """
    Model representing an import process for various sales channel data.
    """
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.sales_channel} - {self.get_status_display()}"


class ImportProperty(ImportableModel):
    """
    Model representing the import process for properties.
    """

    remote_property = models.ForeignKey(RemoteProperty, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportProperty for {self.remote_property}"

class ImportPropertySelectValue(ImportableModel):
    """
    Model representing the import process for property select values.
    """

    remote_property_value = models.ForeignKey(RemotePropertySelectValue, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportPropertySelectValue for {self.remote_property_value}"

class ImportProduct(ImportableModel):
    """
    Model representing the import process for products.
    """

    remote_product = models.ForeignKey(RemoteProduct, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportProduct for {self.remote_product}"

class ImportVat(ImportableModel):
    """
    Model representing the import process for VAT (tax) rates.
    """

    remote_vat = models.ForeignKey(RemoteVat, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportVat for {self.remote_vat}"

class ImportCurrency(ImportableModel):
    """
    Model representing the import process for currencies.
    """

    remote_currency = models.ForeignKey(RemoteCurrency, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportCurrency for {self.remote_currency}"

class ImportImage(ImportableModel):
    """
    Model representing the import process for images.
    """

    remote_image = models.ForeignKey(RemoteImage, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportImage for {self.remote_image}"
