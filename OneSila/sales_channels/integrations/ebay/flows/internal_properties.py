from sales_channels.integrations.ebay.constants import EBAY_INTERNAL_PROPERTY_DEFAULTS
from sales_channels.integrations.ebay.models import (
    EbayInternalProperty,
    EbayInternalPropertyOption,
)


def _ensure_internal_property_options(*, internal_property, sales_channel, options):
    if not options:
        return

    existing_values = set(
        internal_property.options.values_list('value', flat=True)
    )

    for index, option in enumerate(options):
        value = option['value']
        if value in existing_values:
            continue

        EbayInternalPropertyOption.objects.create(
            internal_property=internal_property,
            sales_channel=sales_channel,
            multi_tenant_company=sales_channel.multi_tenant_company,
            value=value,
            label=option.get('label', value.title()),
            description=option.get('description', ''),
            sort_order=option.get('sort_order', index),
        )


def ensure_internal_properties_flow(sales_channel):
    """Ensure default internal properties exist for the given sales channel."""
    for definition in EBAY_INTERNAL_PROPERTY_DEFAULTS:
        internal_property, _ = EbayInternalProperty.objects.get_or_create(
            multi_tenant_company=sales_channel.multi_tenant_company,
            sales_channel=sales_channel,
            code=definition['code'],
            defaults={
                'name': definition['name'],
                'type': definition['type'],
                'is_root': definition['is_root'],
            },
        )
        _ensure_internal_property_options(
            internal_property=internal_property,
            sales_channel=sales_channel,
            options=definition.get('options', []),
        )
