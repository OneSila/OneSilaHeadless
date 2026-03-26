from django.core.validators import FileExtensionValidator

from core import models
from core.upload_paths import tenant_upload_to
from get_absolute_url.helpers import generate_absolute_url
from sales_channels.models.imports import SalesChannelImport


class MiraklSalesChannelImport(SalesChannelImport):
    """Mirakl import process entry used for schema/product imports only."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCTS = "products"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCTS, "Products"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    def __str__(self) -> str:
        hostname = getattr(self.sales_channel, "hostname", "") or "Mirakl"
        import_type = self.get_type_display() if self.type else "Import"
        percentage = getattr(self, "percentage", 0) or 0
        return f"{hostname} | {import_type} | {percentage}%"

    class Meta:
        verbose_name = "Mirakl Sales Channel Import"
        verbose_name_plural = "Mirakl Sales Channel Imports"


class MiraklSalesChannelImportExportFile(models.Model):
    """Uploaded Mirakl catalog export file associated with a Mirakl import."""

    import_process = models.ForeignKey(
        "mirakl.MiraklSalesChannelImport",
        on_delete=models.CASCADE,
        related_name="export_files",
    )
    file = models.FileField(
        upload_to=tenant_upload_to("mirakl_imports"),
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])],
        help_text="Uploaded Mirakl catalog export file in .xlsx format.",
    )

    @property
    def file_url(self) -> str | None:
        if not self.file:
            return None
        try:
            return f"{generate_absolute_url(trailing_slash=False)}{self.file.url}"
        except ValueError:
            return None

    def __str__(self) -> str:
        filename = getattr(getattr(self, "file", None), "name", "") or "Unnamed file"
        return f"{self.import_process_id} | {filename}"

    class Meta:
        verbose_name = "Mirakl Sales Channel Import Export File"
        verbose_name_plural = "Mirakl Sales Channel Import Export Files"
