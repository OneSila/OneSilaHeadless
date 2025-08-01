import math
from django.db import transaction
from django.db.models import F

from .models import Import


def increment_processed_records(process_id: int, delta: int = 1) -> None:
    """Safely increment the processed counter and update percentage."""
    Import.objects.filter(pk=process_id).update(processed_records=F('processed_records') + delta)
    imp = Import.objects.get(pk=process_id)
    if imp.total_records:
        percent = math.floor((imp.processed_records / imp.total_records) * 100)
        Import.objects.filter(pk=process_id).update(percentage=percent)


def append_broken_record(process_id: int, record: dict) -> None:
    """Safely append a broken record to the import process."""
    with transaction.atomic():
        imp = Import.objects.select_for_update().get(pk=process_id)
        data = imp.broken_records or []
        data.append(record)
        imp.broken_records = data
        imp.save(update_fields=['broken_records'])

