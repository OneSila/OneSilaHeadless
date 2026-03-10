from core import models
from sales_channels.models.products import RemoteEanCode, RemotePrice, RemoteProduct, RemoteProductContent


class MiraklProduct(RemoteProduct):
    """Mirakl remote catalog product mirror."""

    product_id_type = models.CharField(max_length=64, blank=True, default="")
    product_reference = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=512, blank=True, default="")
    brand = models.CharField(max_length=255, blank=True, default="")
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Product"
        verbose_name_plural = "Mirakl Products"


class MiraklPrice(RemotePrice):
    """Mirakl price mirror."""

    class Meta:
        verbose_name = "Mirakl Price"
        verbose_name_plural = "Mirakl Prices"


class MiraklProductContent(RemoteProductContent):
    """Mirakl product content mirror."""

    class Meta:
        verbose_name = "Mirakl Product Content"
        verbose_name_plural = "Mirakl Product Contents"


class MiraklEanCode(RemoteEanCode):
    """Mirakl EAN / identifier mirror."""

    class Meta:
        verbose_name = "Mirakl EAN Code"
        verbose_name_plural = "Mirakl EAN Codes"
