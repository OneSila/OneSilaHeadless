from core import models
from sales_channels.models.logs import RemoteLog


class AmazonRemoteLog(RemoteLog):
    """Remote log extended with Amazon submission details."""

    submission_id = models.CharField(max_length=255, null=True, blank=True)
    issues = models.JSONField(null=True, blank=True)
    processing_status = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        verbose_name = "Amazon Remote Log"
        verbose_name_plural = "Amazon Remote Logs"
        ordering = ["-created_at"]
