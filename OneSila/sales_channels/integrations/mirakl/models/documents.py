from core import models
from sales_channels.models.documents import RemoteDocumentType


class MiraklDocumentType(RemoteDocumentType):
    """Mirakl document type placeholder."""

    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Document Type"
        verbose_name_plural = "Mirakl Document Types"
