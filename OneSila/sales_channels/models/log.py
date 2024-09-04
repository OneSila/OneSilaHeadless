from core import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class RemoteLog(models.Model):
    """
    A generic log model to track actions related to various objects in the system.
    All the models that will have RemoteObjectMixin will have special methods to create this logs for EVERY SINGLE API REQUEST
    This gives us full control over any error / any api request that was made from our system and full traceability
    """

    # Constants for action choices
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]

    # Constants for status choices
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    sales_channel = models.ForeignKey('SalesChannel', on_delete=models.PROTECT)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)
    payload = models.JSONField(null=True, blank=True, help_text="The API call payload associated with this log.")
    response = models.TextField(null=True, blank=True, help_text="The API response or additional information.")
    error_traceback = models.TextField(null=True, blank=True, help_text="Detailed error traceback if the action failed.")
    user_error = models.BooleanField(default=False)  # Boolean field to indicate if the error is user-facing
    identifier = models.CharField(max_length=255, null=True, blank=True)  # Field to store a unique identifier for the log entry
    keep = models.BooleanField(default=False, help_text="Whether to keep this log permanently.")

    class Meta:
        verbose_name = 'Remote Log'
        verbose_name_plural = 'Remote Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Log for {self.content_object} - Action: {self.action}, Status: {self.status}"