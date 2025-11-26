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
from core.upload_paths import tenant_upload_to


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
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional human-readable name for the import process.",
    )
    error_traceback = models.TextField(
        null=True,
        blank=True,
        help_text="Stores the error traceback if the import fails."
    )
    create_only = models.BooleanField(
        default=False,
        help_text="If True, existing objects fetched during the import will not be updated.",
    )
    update_only = models.BooleanField(
        default=False,
        help_text="If True, the import will only update existing objects and fail if they do not exist.",
    )
    skip_broken_records = models.BooleanField(
        default=False,
        help_text="If True, the import will skip records that raise errors and continue processing."
    )
    broken_records = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array storing details of records that failed during import."
    )
    total_records = models.PositiveIntegerField(
        default=0,
        help_text="Total number of items that this import will process.",
    )
    processed_records = models.PositiveIntegerField(
        default=0,
        help_text="How many items have been processed so far in async imports.",
    )

    def get_cleaned_errors_from_broken_records(self):
        import re
        from django.core.exceptions import ObjectDoesNotExist
        from products.models import Product

        cleaned_errors = []
        broken_records = self.broken_records
        company = self.multi_tenant_company

        custom_error_starts = [
            "Parent product must be of type CONFIGURABLE.",
            "Variation product must be of type SIMPLE or BUNDLE or ALIAS.",
            "Parent product must be of type BUNDLE.",
        ]

        def matches_custom_save_error(msg):
            return any(msg.strip().startswith(pattern) for pattern in custom_error_starts)

        def find_sku_and_type(data, target_sku):
            if data.get("sku") == target_sku:
                return data.get("type"), data.get("alias_parent_sku")
            for key in ["variations", "bundle_variations", "alias_variations"]:
                for var in data.get(key, []):
                    var_data = var.get("variation_data", {})
                    if var_data.get("sku") == target_sku:
                        return var_data.get("type"), var_data.get("alias_parent_sku")
            return None, None

        for record in broken_records:
            error_msg = record.get("error", "")
            data = record.get("data", {})

            if matches_custom_save_error(error_msg):
                cleaned_errors.append(error_msg)
                continue

            match_alias_detail = re.search(
                r'Failing row contains\s*\((.*?)\)', error_msg, re.DOTALL
            )
            if match_alias_detail:
                row = match_alias_detail.group(1)
                parts = [p.strip() for p in row.split(',')]
                if len(parts) >= 4:
                    sku = parts[3]
                    feed_type, alias_parent_sku = find_sku_and_type(data, sku)
                    if alias_parent_sku:
                        cleaned_errors.append(
                            f"Alias product for SKU {sku} is linked to the product with SKU: {alias_parent_sku} that doesn't exist."
                        )
                    else:
                        cleaned_errors.append(
                            f"Alias product for SKU {sku} is linked to a product that doesn't exist (could not find alias_parent_sku in data)."
                        )
                    continue

            match_duplicate = re.search(
                r'Key \(sku, multi_tenant_company_id\)=\(([^,\n]+),', error_msg
            )
            if match_duplicate:
                sku = match_duplicate.group(1).strip()
                feed_type, _ = find_sku_and_type(data, sku)
                try:
                    local_product_type = Product.objects.get(multi_tenant_company=company, sku=sku).type
                except ObjectDoesNotExist:
                    local_product_type = "NOT FOUND"

                cleaned_errors.append(
                    f"SKU {sku} has wrong product type in data feed ({feed_type}). In OneSila this is marked as {local_product_type}"
                )
                continue

            if not matches_custom_save_error(error_msg):
                cleaned_errors.append("Unknown error format")

        return cleaned_errors

    def __str__(self):
        base = f"{self.get_status_display()} ({self.percentage}%)"
        return f"{self.name or 'ImportProcess'} - {base}"

    class Meta:
        ordering = ['-created_at']


class ImportBrokenRecord(models.Model):
    """Store broken records generated during an import process."""

    import_process = models.ForeignKey(
        'imports_exports.Import',
        on_delete=models.CASCADE,
        related_name='broken_record_entries'
    )
    record = models.JSONField(
        blank=True,
        help_text="Store broken record that failed during import."
    )

    class Meta:
        verbose_name = "Import Broken Record"
        verbose_name_plural = "Import Broken Records"



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
        upload_to=tenant_upload_to("mapped_imports"),
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


class ImportReport(models.Model):
    """Stores email report information for an :class:`Import`."""

    import_process = models.ForeignKey(
        Import,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    users = models.ManyToManyField(
        'core.MultiTenantUser',
        blank=True,
        help_text="Internal users that will receive a report.",
    )
    external_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="List of external emails that will receive a report.",
    )

    def clean(self):
        super().clean()
        company = self.import_process.multi_tenant_company

        # this will need refactor at some point
        if self.pk:
            invalid = self.users.exclude(multi_tenant_company=company)
            if invalid.exists():
                raise ValidationError(
                    "All users must belong to the same company as the import process."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
