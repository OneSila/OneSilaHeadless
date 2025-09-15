import math
from django.db import transaction
from django.db.models import F, Case, When, IntegerField
from django.db.models.functions import Cast

from sales_channels.integrations.amazon.models import AmazonImportBrokenRecord
from .models import Import


def increment_processed_records(process_id: int, delta: int = 1) -> None:
    """Safely increment the processed counter and update percentage."""
    Import.objects.filter(pk=process_id).update(
        processed_records=F("processed_records") + delta,
        percentage=Case(
            When(
                total_records__gt=0,
                then=Cast(
                    ((F("processed_records") + delta) * 100) / F("total_records"),
                    IntegerField(),
                ),
            ),
            default=F("percentage"),
            output_field=IntegerField(),
        ),
    )


def append_broken_record(process_id: int, record: dict) -> None:
    """Safely append a broken record to the import process."""
    imp = Import.objects.get(pk=process_id)
    AmazonImportBrokenRecord.objects.create(
        multi_tenant_company=imp.multi_tenant_company,
        import_process=imp,
        record=record,
    )