from sales_channels.integrations.ebay.constants import EBAY_DOCUMENT_TYPE_DEFAULTS
from sales_channels.integrations.ebay.models import EbayDocumentType


def ensure_ebay_document_types_flow(*, sales_channel):
    """Ensure default eBay document types exist for the given sales channel."""
    for definition in EBAY_DOCUMENT_TYPE_DEFAULTS:
        remote_id = str(definition.get("value") or "").strip()
        if not remote_id:
            continue

        defaults = {
            "name": definition.get("name"),
            "description": definition.get("description"),
        }

        document_type, _ = EbayDocumentType.objects.get_or_create(
            multi_tenant_company=sales_channel.multi_tenant_company,
            sales_channel=sales_channel,
            remote_id=remote_id,
            defaults=defaults,
        )

        updates = []
        expected_name = defaults.get("name")
        if expected_name is not None and document_type.name != expected_name:
            document_type.name = expected_name
            updates.append("name")

        expected_description = defaults.get("description")
        if expected_description is not None and document_type.description != expected_description:
            document_type.description = expected_description
            updates.append("description")

        if updates:
            document_type.save(update_fields=updates)
