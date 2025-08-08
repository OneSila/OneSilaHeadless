from core import models
from core.helpers import ensure_serializable
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

    product_owner = models.BooleanField(
        default=False,
        help_text="Indicates if this listing was created by us and we can manage listing level data.",
    )

    @property
    def remote_type(self):
        return self.get_remote_rule().product_type_code

    def get_remote_rule(self):
        from sales_channels.integrations.amazon.models import AmazonProductType

        local_rule = self.local_instance.get_product_rule()
        if local_rule is None:
            raise Exception("Product rule not found.")

        return AmazonProductType.objects.get(
            local_instance=local_rule,
            sales_channel=self.sales_channel,
        )

    def get_issues(self, view, is_validation=None):
        """Return serialized issues for this product in a given marketplace."""
        from sales_channels.integrations.amazon.models import AmazonProductIssue

        qs = AmazonProductIssue.objects.filter(remote_product=self, view=view)
        if is_validation is not None:
            qs = qs.filter(is_validation_issue=is_validation)

        issues = []
        for issue in qs:
            issues.append(
                ensure_serializable(
                    {
                        "code": issue.code,
                        "message": issue.message,
                        "severity": issue.severity,
                        "is_validation_issue": issue.is_validation_issue,
                        "raw_data": issue.raw_data,
                    }
                )
            )

        return issues


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
    imported_url = models.URLField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="Original URL of the image when imported from Amazon.",
    )


class AmazonCategory(RemoteCategory):
    """Amazon remote category."""
    pass


class AmazonEanCode(RemoteEanCode):
    """Amazon remote EAN codes."""

    class Meta:
        verbose_name = 'Amazon EAN Code'
        verbose_name_plural = 'Amazon EAN Codes'
