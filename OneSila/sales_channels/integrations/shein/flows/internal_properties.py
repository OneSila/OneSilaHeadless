import logging
from typing import Any, Iterable

from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
)


logger = logging.getLogger(__name__)


class SheinInternalPropertiesFlow(SheinSignatureMixin):
    """Ensure canonical Shein payload fields and enumerations exist."""

    brand_list_path = "/open-api/goods/query-brand-list"

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel

    def run(self) -> None:
        self._ensure_internal_properties()
        self._sync_brand_options()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_internal_properties(self) -> None:
        for definition in constants.SHEIN_INTERNAL_PROPERTY_DEFINITIONS:
            SheinInternalProperty.objects.update_or_create(
                sales_channel=self.sales_channel,
                code=definition['code'],
                defaults={
                    'multi_tenant_company': self.sales_channel.multi_tenant_company,
                    'name': str(definition['name']),
                    'type': definition['type'],
                    'is_root': definition.get('is_root', False),
                    'payload_field': definition.get('payload_field', '') or '',
                },
            )

    def _sync_brand_options(self) -> None:
        try:
            internal_property = SheinInternalProperty.objects.get(
                sales_channel=self.sales_channel,
                code='brand_code',
            )
        except SheinInternalProperty.DoesNotExist:
            return

        brand_records = self._fetch_brand_records()
        if not brand_records:
            return

        existing_options = {
            option.value: option
            for option in internal_property.options.all()
        }
        active_values: set[str] = set()

        for sort_order, record in enumerate(brand_records):
            value = self._normalize_identifier(record.get('brand_code'))
            if not value:
                continue

            label = self._safe_string(record.get('brand_name')) or value
            option, _ = SheinInternalPropertyOption.objects.update_or_create(
                internal_property=internal_property,
                value=value,
                defaults={
                    'sales_channel': self.sales_channel,
                    'multi_tenant_company': self.sales_channel.multi_tenant_company,
                    'label': label,
                    'description': '',
                    'sort_order': sort_order,
                    'is_active': True,
                    'raw_data': record,
                },
            )
            existing_options.pop(option.value, None)
            active_values.add(option.value)

        # Soft disable options that disappeared remotely
        if existing_options:
            SheinInternalPropertyOption.objects.filter(
                pk__in=[option.pk for option in existing_options.values()],
            ).update(is_active=False)

    # ------------------------------------------------------------------
    # Remote helpers
    # ------------------------------------------------------------------
    def _fetch_brand_records(self) -> list[dict[str, Any]]:
        try:
            response = self.shein_post(path=self.brand_list_path, payload={})
        except ValueError:
            logger.warning(
                "Unable to fetch Shein brand list for channel %s",
                getattr(self.sales_channel, 'pk', 'unknown'),
            )
            return []

        try:
            data = response.json()
        except ValueError:
            logger.warning(
                "Invalid JSON returned from Shein brand list for channel %s",
                getattr(self.sales_channel, 'pk', 'unknown'),
            )
            return []

        if not isinstance(data, dict):
            return []

        info = data.get('info')
        if not isinstance(info, dict):
            return []

        records = info.get('data')
        if not isinstance(records, Iterable):
            return []

        return [record for record in records if isinstance(record, dict)]

    # ------------------------------------------------------------------
    # Small utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_string(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_identifier(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


def ensure_internal_properties_flow(sales_channel) -> None:
    """Public helper invoked by signals to ensure internal metadata exists."""

    flow = SheinInternalPropertiesFlow(sales_channel=sales_channel)
    try:
        flow.run()
    except ValueError:
        # Raised when credentials are missing. Defer execution until OAuth completes.
        logger.info(
            "Skipping Shein internal property sync for channel %s due to missing credentials",
            getattr(sales_channel, 'pk', 'unknown'),
        )
