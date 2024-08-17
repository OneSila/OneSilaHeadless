from core import models
from polymorphic.models import PolymorphicModel
from sales_channels.models.sales_channels import SalesChannel
from .product import (
    RemoteProduct,
    RemoteImage,
)
from .property import RemoteProperty, RemotePropertySelectValue
from .taxes import RemoteVat, RemoteCurrency

class ImportProcess(PolymorphicModel, models.Model):
    """
    Model representing an import process for various sales channel data.
    """

    TYPE_PROPERTIES = 'properties'
    TYPE_PROPERTY_VALUES = 'property_values'
    TYPE_PRODUCTS = 'products'
    TYPE_TAXES = 'taxes'
    TYPE_CURRENCIES = 'currencies'
    TYPE_IMAGES = 'images'

    TYPE_CHOICES = [
        (TYPE_PROPERTIES, 'Properties'),
        (TYPE_PROPERTY_VALUES, 'Property Values'),
        (TYPE_PRODUCTS, 'Products'),
        (TYPE_TAXES, 'Taxes'),
        (TYPE_CURRENCIES, 'Currencies'),
        (TYPE_IMAGES, 'Images'),
    ]

    STATUS_FAILED = 'failed'
    STATUS_SUCCESS = 'success'

    STATUS_CHOICES = [
        (STATUS_FAILED, 'Failed'),
        (STATUS_SUCCESS, 'Success'),
    ]

    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of the import process completed.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_FAILED)
    error_traceback = models.TextField(null=True, blank=True, help_text="Stores the error traceback if the import fails.")

    def __str__(self):
        return f"ImportProcess {self.type} for {self.sales_channel} - {self.get_status_display()}"

class ImportableModel(PolymorphicModel, models.Model):
    """
    Abstract model for representing importable data with a reference to raw data and the import process.
    """

    raw_data = models.JSONField(help_text="The raw data being imported.")
    import_process = models.ForeignKey(ImportProcess, on_delete=models.CASCADE)

    class Meta:
        abstract = True

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
