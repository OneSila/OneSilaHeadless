from sales_channels.integrations.ebay.constants import EBAY_INTERNAL_PROPERTY_DEFAULTS
from sales_channels.integrations.ebay.models import EbayInternalProperty


def ensure_internal_properties_flow(sales_channel):
    """Ensure default internal properties exist for the given sales channel."""
    for definition in EBAY_INTERNAL_PROPERTY_DEFAULTS:
        EbayInternalProperty.objects.get_or_create(
            sales_channel=sales_channel,
            code=definition['code'],
            defaults={
                'label': definition['label'],
                'type': definition['type'],
                'is_root': definition['is_root'],
            },
        )
