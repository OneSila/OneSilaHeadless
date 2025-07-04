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

    # keep track of which marketplace listings have been created
    created_marketplaces = models.JSONField(
        default=list,
        blank=True,
        help_text="List of Amazon marketplace IDs where the product was created.",
    )

    # store the EAN code used on creation as it cannot be changed later
    ean_code = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        help_text="EAN code used when the product was first created.",
    )

    @property
    def remote_type(self):
        from sales_channels.integrations.amazon.models import AmazonProductType

        local_rule = self.local_instance.get_product_rule()
        if local_rule is None:
            raise Exception("Product rule not found.")

        remote_rule = AmazonProductType.objects.get(
            local_instance=local_rule,
            sales_channel=self.sales_channel,
        )

        return remote_rule.product_type_code

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
