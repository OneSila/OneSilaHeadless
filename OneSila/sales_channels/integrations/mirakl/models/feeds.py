from core import models
from core.upload_paths import tenant_upload_to
from get_absolute_url.helpers import generate_absolute_url

from sales_channels.models.feeds import SalesChannelFeed


class MiraklSalesChannelFeed(SalesChannelFeed):
    """Mirakl-specific feed batch artifact."""

    STAGE_PRODUCT = "product"
    STAGE_OFFER = "offer"

    STAGE_CHOICES = [
        (STAGE_PRODUCT, "Product"),
        (STAGE_OFFER, "Offer"),
    ]

    stage = models.CharField(max_length=32, choices=STAGE_CHOICES, default=STAGE_PRODUCT)
    product_remote_id = models.CharField(max_length=255, blank=True, default="")
    offer_remote_id = models.CharField(max_length=255, blank=True, default="")
    raw_data = models.JSONField(default=dict, blank=True)
    import_status = models.CharField(max_length=64, blank=True, default="")
    reason_status = models.CharField(max_length=128, blank=True, default="")
    remote_date_created = models.DateTimeField(null=True, blank=True)
    remote_shop_id = models.BigIntegerField(null=True, blank=True)
    has_error_report = models.BooleanField(default=False)
    has_new_product_report = models.BooleanField(default=False)
    has_transformation_error_report = models.BooleanField(default=False)
    has_transformed_file = models.BooleanField(default=False)
    transform_lines_read = models.PositiveIntegerField(default=0)
    transform_lines_in_success = models.PositiveIntegerField(default=0)
    transform_lines_in_error = models.PositiveIntegerField(default=0)
    transform_lines_with_warning = models.PositiveIntegerField(default=0)
    error_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    new_product_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    transformed_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    transformation_error_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)

    class Meta:
        verbose_name = "Mirakl Sales Channel Feed"
        verbose_name_plural = "Mirakl Sales Channel Feeds"

    def _get_file_url(self, *, field_name: str) -> str | None:
        file_field = getattr(self, field_name, None)
        if not file_field:
            return None
        try:
            return f"{generate_absolute_url(trailing_slash=False)}{file_field.url}"
        except ValueError:
            return None

    @property
    def error_report_file_url(self) -> str | None:
        return self._get_file_url(field_name="error_report_file")

    @property
    def new_product_report_file_url(self) -> str | None:
        return self._get_file_url(field_name="new_product_report_file")

    @property
    def transformed_file_url(self) -> str | None:
        return self._get_file_url(field_name="transformed_file")

    @property
    def transformation_error_report_file_url(self) -> str | None:
        return self._get_file_url(field_name="transformation_error_report_file")
