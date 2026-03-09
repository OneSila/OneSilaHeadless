import math
import ipaddress
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Case, When, IntegerField, Value
from django.db.models.functions import Cast, Least

from sales_channels.integrations.amazon.models import AmazonImportBrokenRecord
from .models import Import, ImportBrokenRecord


def validate_external_fetch_url(*, url: str, label: str):
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme != "https":
        raise ValidationError(f"Only HTTPS {label} URLs are allowed.")

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        raise ValidationError(f"Invalid {label} URL host.")

    port = parsed.port
    if port not in (None, 443):
        raise ValidationError(f"Only standard HTTPS ports are allowed for {label} imports.")

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValidationError(f"Localhost URLs are not allowed for {label} imports.")

    try:
        parsed_ip = ipaddress.ip_address(hostname)
    except ValueError:
        parsed_ip = None

    if parsed_ip and (
        parsed_ip.is_private
        or parsed_ip.is_loopback
        or parsed_ip.is_link_local
        or parsed_ip.is_multicast
        or parsed_ip.is_reserved
        or parsed_ip.is_unspecified
    ):
        raise ValidationError(f"Private or reserved IP addresses are not allowed for {label} imports.")

    return parsed


def increment_processed_records(process_id: int, delta: int = 1) -> None:
    """Safely increment the processed counter and update percentage."""
    Import.objects.filter(pk=process_id).update(
        processed_records=F("processed_records") + delta,
        percentage=Case(
            When(
                total_records__gt=0,
                then=Least(
                    Cast(
                        ((F("processed_records") + delta) * 100) / F("total_records"),
                        IntegerField(),
                    ),
                    Value(100),
                    output_field=IntegerField(),
                ),
            ),
            default=F("percentage"),
            output_field=IntegerField(),
        ),
    )


def append_amazon_broken_record(process_id: int, record: dict) -> None:
    """Safely append a broken record to the import process."""
    imp = Import.objects.get(pk=process_id)
    AmazonImportBrokenRecord.objects.create(
        multi_tenant_company=imp.multi_tenant_company,
        import_process=imp,
        record=record,
    )

def append_broken_record(process_id: int, record: dict) -> None:
    """Safely append a broken record to the import process."""
    imp = Import.objects.get(pk=process_id)
    ImportBrokenRecord.objects.create(
        multi_tenant_company=imp.multi_tenant_company,
        import_process=imp,
        record=record,
    )
