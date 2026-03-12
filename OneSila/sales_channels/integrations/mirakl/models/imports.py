from core import models
from core.upload_paths import tenant_upload_to
from get_absolute_url.helpers import generate_absolute_url
from sales_channels.models.imports import SalesChannelImport


class MiraklSalesChannelImport(SalesChannelImport):
    """Mirakl async import tracking."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCT = "product"
    TYPE_OFFER = "offer"
    TYPE_PRICING = "pricing"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCT, "Product"),
        (TYPE_OFFER, "Offer"),
        (TYPE_PRICING, "Pricing"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    remote_import_id = models.CharField(max_length=255, blank=True, default="")
    source_file_name = models.CharField(max_length=255, blank=True, default="")
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
    summary_data = models.JSONField(default=dict, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    offer_response = models.JSONField(default=dict, blank=True)
    feed = models.ForeignKey(
        "sales_channels.SalesChannelFeed",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mirakl_imports",
    )
    error_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    new_product_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    transformed_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)
    transformation_error_report_file = models.FileField(upload_to=tenant_upload_to("mirakl_imports"), null=True, blank=True)

    class Meta:
        verbose_name = "Mirakl Sales Channel Import"
        verbose_name_plural = "Mirakl Sales Channel Imports"

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
