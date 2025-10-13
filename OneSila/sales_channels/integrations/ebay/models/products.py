from django.utils.translation import gettext_lazy as _

from core import models
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.products import (
    RemoteProduct,
    RemotePrice,
    RemoteProductContent,
    RemoteImageProductAssociation,
    RemoteEanCode,
)

class EbayProduct(RemoteProduct):
    """eBay product model."""
    pass


class EbayMediaThroughProduct(RemoteImageProductAssociation):
    """eBay media through product model."""
    pass


class EbayPrice(RemotePrice):
    """eBay price model."""
    pass


class EbayProductContent(RemoteProductContent):
    """eBay product content model."""
    pass


class EbayEanCode(RemoteEanCode):
    """eBay EAN code model."""
    pass


class EbayProductOffer(RemoteObjectMixin, models.Model):
    """Track offer metadata per eBay remote product and marketplace view."""

    remote_product = models.ForeignKey(
        'ebay.EbayProduct',
        on_delete=models.CASCADE,
        related_name='offers',
        help_text="Remote product this offer belongs to.",
    )
    sales_channel_view = models.ForeignKey(
        'ebay.EbaySalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_offers',
        help_text="Marketplace view associated with this offer.",
    )
    listing_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Listing identifier returned by eBay.",
    )
    listing_status = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="Current status of the linked listing, if available.",
    )

    class Meta:
        unique_together = ("remote_product", "sales_channel_view")
        verbose_name = _("eBay Product Offer")
        verbose_name_plural = _("eBay Product Offers")

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        forced_fields: set[str] = set()

        if self.remote_product_id and not self.sales_channel_id:
            self.sales_channel = self.remote_product.sales_channel
            forced_fields.add("sales_channel")

        expected_company = None
        if self.remote_product_id and hasattr(self.remote_product, "multi_tenant_company"):
            expected_company = getattr(self.remote_product, "multi_tenant_company", None)
        if expected_company and getattr(self, "multi_tenant_company_id", None) != getattr(expected_company, "id", None):
            self.multi_tenant_company = expected_company
            forced_fields.add("multi_tenant_company")

        if forced_fields and update_fields is not None:
            kwargs["update_fields"] = list(set(update_fields) | forced_fields)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        offer_id = self.remote_id or "—"
        view_code = getattr(self.sales_channel_view, "remote_id", None) or "view"
        return f"Offer {offer_id} for {self.remote_product} @ {view_code}"
