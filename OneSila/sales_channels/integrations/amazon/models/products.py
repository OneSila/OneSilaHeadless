from core import models
from sales_channels.models.products import (
    RemoteProduct,
    RemoteInventory,
    RemotePrice,
    RemoteProductContent,
    RemoteImageProductAssociation,
    RemoteCategory,
    RemoteEanCode,
)


class AmazonProduct(RemoteProduct):
    """Amazon specific remote product."""

    asin = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="ASIN identifier for the product.",
    )


class AmazonInventory(RemoteInventory):
    """Amazon specific remote inventory."""
    pass


class AmazonPrice(RemotePrice):
    """Amazon specific remote price."""
    pass


class AmazonProductContent(RemoteProductContent):
    """Amazon specific remote product content."""
    pass


class AmazonImageProductAssociation(RemoteImageProductAssociation):
    """Association between images and Amazon products."""
    pass


class AmazonCategory(RemoteCategory):
    """Amazon remote category."""
    pass


class AmazonEanCode(RemoteEanCode):
    """Amazon remote EAN codes."""

    class Meta:
        verbose_name = 'Amazon EAN Code'
        verbose_name_plural = 'Amazon EAN Codes'
