from core import models
from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Import(PolymorphicModel, models.Model):
    """
    Model representing an import process.
    Note: Removed the 'type' and 'sales_channel' fields.
    """

    STATUS_FAILED = 'failed'
    STATUS_PROCESSING = 'processing'
    STATUS_SUCCESS = 'success'

    STATUS_CHOICES = [
        (STATUS_FAILED, 'Failed'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SUCCESS, 'Success'),
    ]

    percentage = models.PositiveIntegerField(
        default=0,
        help_text="Whole integer representing the import process progress."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_FAILED
    )
    error_traceback = models.TextField(
        null=True,
        blank=True,
        help_text="Stores the error traceback if the import fails."
    )

    def __str__(self):
        return f"ImportProcess - {self.get_status_display()} ({self.percentage}%)"


class ImportableModel(PolymorphicModel, models.Model):
    """
    Abstract model for representing importable data.
    This model serves as a log that stores both raw and structured data,
    and also creates a link (via a GenericForeignKey) to the target instance that is created from this import.
    """

    raw_data = models.JSONField(
        help_text="The raw data being imported."
    )
    structured_data = models.JSONField(
        help_text="The structured data after processing the raw data."
    )
    import_process = models.ForeignKey(
        Import,
        on_delete=models.CASCADE
    )
    successfully_imported = models.BooleanField(
        default=False,
        help_text="Indicates if the data was successfully imported."
    )

    # Generic foreign key to the created target instance (e.g., a property value or similar)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    target_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True

    def __str__(self):
        return f"ImportableModel log for process: {self.import_process}"