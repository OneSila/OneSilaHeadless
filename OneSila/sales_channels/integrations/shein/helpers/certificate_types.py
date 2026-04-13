from __future__ import annotations

PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER = "SheinExternalDocumentsPending"
RESOLVED_EXTERNAL_DOCUMENTS_IDENTIFIER = "SheinExternalDocumentsResolved"


def is_certificate_type_uploadable(
    *,
    sales_channel,
    certificate_type_id: str,
) -> bool:
    normalized_certificate_type_id = str(certificate_type_id or "").strip()
    if not normalized_certificate_type_id:
        return True

    if sales_channel is None or getattr(sales_channel, "pk", None) is None:
        return True

    from sales_channels.integrations.shein.models import SheinDocumentType

    uploadable = (
        SheinDocumentType.objects.filter(
            sales_channel=sales_channel,
            remote_id=normalized_certificate_type_id,
        )
        .values_list("uploadable", flat=True)
        .first()
    )
    if uploadable is None:
        return True
    return bool(uploadable)
