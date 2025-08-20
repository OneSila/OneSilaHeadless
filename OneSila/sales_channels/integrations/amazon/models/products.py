from core import models
from core.helpers import ensure_serializable
from django.core.exceptions import ValidationError
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

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last sync with Amazon.",
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


class AmazonExternalProductId(models.Model):
    """Store merchant-provided ASIN per marketplace."""

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='amazon_merchant_asins',
        help_text='The product this ASIN belongs to.',
    )
    view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_asins',
        help_text='Marketplace for this ASIN.',
    )
    asin = models.CharField(max_length=32)

    class Meta:
        unique_together = ("product", "view")
        verbose_name = 'Amazon Merchant ASIN'
        verbose_name_plural = 'Amazon Merchant ASINs'


class AmazonGtinExemption(models.Model):
    """Store GTIN exemption flag per marketplace."""

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='amazon_gtin_exemptions',
        help_text='The product this exemption belongs to.',
    )
    view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_gtin_exemptions',
        help_text='Marketplace for this exemption.',
    )
    value = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "view")
        verbose_name = 'Amazon GTIN Exemption'
        verbose_name_plural = 'Amazon GTIN Exemptions'


class AmazonVariationTheme(models.Model):
    """Store variation theme per marketplace."""

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='amazon_variation_themes',
        help_text='The product this variation theme belongs to.',
    )
    view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_variation_themes',
        help_text='Marketplace for this variation theme.',
    )
    theme = models.CharField(max_length=64)

    class Meta:
        unique_together = ("product", "view")
        verbose_name = 'Amazon Variation Theme'
        verbose_name_plural = 'Amazon Variation Themes'

    def clean(self):
        from products.models import Product as LocalProduct
        from sales_channels.integrations.amazon.models import AmazonProductType

        if self.product.type != LocalProduct.CONFIGURABLE:
            raise ValidationError("Variation themes are only allowed for configurable products.")

        rule = self.product.get_product_rule()
        if rule is None:
            raise ValidationError("Product type not set.")

        try:
            remote_rule = AmazonProductType.objects.get(
                local_instance=rule,
                sales_channel=self.view.sales_channel,
            )
        except AmazonProductType.DoesNotExist as e:
            raise ValidationError("Amazon product type not found.") from e

        themes = remote_rule.variation_themes or []
        if self.theme not in themes:
            raise ValidationError("Invalid variation theme for product type.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
