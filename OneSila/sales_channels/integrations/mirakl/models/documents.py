from core import models
from sales_channels.models.documents import RemoteDocumentType


class MiraklDocumentType(RemoteDocumentType):
    entity = models.CharField(max_length=64, blank=True, default="")
    mime_types = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

