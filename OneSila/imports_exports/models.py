from core import models
from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
import json
import requests
import mimetypes
from django.core.exceptions import ValidationError

from core.helpers import get_languages


class Import(PolymorphicModel, models.Model):
    """
    Model representing an import process.
    Note: Removed the 'type' and 'sales_channel' fields.
    """

    STATUS_NEW = 'new'
    STATUS_PENDING = 'pending'
    STATUS_FAILED = 'failed'
    STATUS_PROCESSING = 'processing'
    STATUS_SUCCESS = 'success'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_PENDING, 'Pending'),
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
        default=STATUS_NEW
    )
    error_traceback = models.TextField(
        null=True,
        blank=True,
        help_text="Stores the error traceback if the import fails."
    )

    def __str__(self):
        return f"ImportProcess - {self.get_status_display()} ({self.percentage}%)"

    class Meta:
        ordering = ['-created_at']


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
        help_text="The structured data after processing the raw data.",
        null=True,
        blank=True,
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


class TypedImport(Import):
    '''
    This is the import that is used to import one batch like property, images but most used will be products
    This can be Mapped (pre mapped we already have the json ready), NotMapped (we need to create the mapper)
    like ExcelImports and many more
    '''
    LANGUAGE_CHOICES = get_languages()

    TYPE_PROPERTY = 'property'
    TYPE_PROPERTY_SELECT_VALUE = 'property_select_value'
    TYPE_PROPERTY_RULE = 'property_rule'
    TYPE_PRODUCT = 'product'

    TYPE_CHOICES = [
        (TYPE_PROPERTY, 'Property'),
        (TYPE_PROPERTY_SELECT_VALUE, 'Property Select Value'),
        (TYPE_PROPERTY_RULE, 'Product Property Rule'),
        (TYPE_PRODUCT, 'Product'),
    ]
    type = models.CharField(
        max_length=32,
        choices=TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="What kind of import this is (e.g., Product, Property, Image...)."
    )

    is_periodic = models.BooleanField(default=False)
    interval_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Repeat interval in hours if this import is periodic."
    )
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this import was last executed."
    )

    language = models.CharField(
        max_length=7,
        choices=LANGUAGE_CHOICES,
        null=True,
        blank=True,
        help_text="Language context for imported records (e.g., en, de, fr)."
    )
    create_only = models.BooleanField(
        default=False,
        help_text="If True, existing objects fetched during the import will not be updated.",
    )

    def should_run(self) -> bool:
        if not self.is_periodic or not self.interval_hours:
            return False
        if not self.last_run_at:
            return True
        return timezone.now() >= self.last_run_at + timedelta(hours=self.interval_hours)

    def mark_as_run(self):
        self.last_run_at = timezone.now()
        self.save(update_fields=["last_run_at"])

    def save(self, *args, **kwargs):
        if not self.pk and self.language is None and hasattr(self, "multi_tenant_company"):
            self.language = getattr(self.multi_tenant_company, "language", None)

        super().save(*args, **kwargs)


    def run(self):
        raise NotImplementedError("Cannot run a TypedImport directly. Use a concrete subclass like MappedImport.")


class MappedImport(TypedImport):
    """
    Import that receives data already mapped to our internal JSON format.
    """

    json_file = models.FileField(
        upload_to="mapped_imports/",
        null=True,
        blank=True,
        help_text="Optional uploaded mapped JSON file."
    )
    json_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL pointing to mapped JSON data."
    )

    def run(self):
        """
        Execute the mapped import using the proper runner.
        """
        from imports_exports.factories.importers import MappedImportRunner

        runner = MappedImportRunner(self)
        runner.run()

        if self.is_periodic:
            self.mark_as_run()
