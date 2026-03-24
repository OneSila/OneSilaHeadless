from core import models
from sales_channels.models.products import RemoteEanCode, RemotePrice, RemoteProduct, RemoteProductContent


class MiraklProduct(RemoteProduct):
    """Mirakl remote catalog product mirror."""

    product_id_type = models.CharField(max_length=64, blank=True, default="")
    product_reference = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=512, blank=True, default="")
    brand = models.CharField(max_length=255, blank=True, default="")
    raw_data = models.JSONField(default=dict, blank=True)

    def _determine_status(self) -> str:
        latest_feed_item = self._get_latest_feed_item()

        if self._has_unresolved_errors():
            return self.STATUS_FAILED
        if self.syncing_current_percentage != 100:
            return self.STATUS_PROCESSING
        if self._has_rejecting_issues():
            return self.STATUS_APPROVAL_REJECTED
        if latest_feed_item is None:
            return self.STATUS_COMPLETED
        if latest_feed_item.status == latest_feed_item.STATUS_SUCCESS:
            return self.STATUS_COMPLETED
        return self.STATUS_PENDING_APPROVAL

    def _has_rejecting_issues(self) -> bool:
        if not self.pk:
            return False
        return self.issues.exclude(severity="WARNING").exists()

    def _get_latest_feed_item(self):
        if not self.pk:
            return None

        from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeedItem

        return (
            MiraklSalesChannelFeedItem.objects.filter(remote_product=self)
            .select_related("feed")
            .order_by("-id")
            .first()
        )

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
