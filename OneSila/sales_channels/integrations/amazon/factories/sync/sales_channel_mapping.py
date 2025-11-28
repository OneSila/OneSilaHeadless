from __future__ import annotations

from typing import Dict, Tuple

from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.amazon.models import (
    AmazonProductType,
    AmazonProperty,
    AmazonPropertySelectValue,
)
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonDefaultUnitConfigurator,
)


class AmazonSalesChannelMappingSyncFactory:
    """Copy Amazon mapping metadata from one sales channel to another."""

    BATCH_SIZE = 25000

    def __init__(
        self,
        *,
        source_sales_channel: AmazonSalesChannel,
        target_sales_channel: AmazonSalesChannel,
    ) -> None:
        self.source_sales_channel = source_sales_channel
        self.target_sales_channel = target_sales_channel

    def run(
        self,
        *,
        sync_product_types: bool = True,
        sync_properties: bool = True,
        sync_select_values: bool = True,
        sync_default_units: bool = True,
    ) -> Dict[str, int]:
        """Execute the sync for the enabled data sets."""
        self._preflight_check()

        summary = {
            "product_types": 0,
            "properties": 0,
            "select_values": 0,
            "default_units": 0,
        }

        if sync_product_types:
            summary["product_types"] = self._sync_product_types()

        if sync_properties:
            summary["properties"] = self._sync_properties()

        if sync_select_values:
            summary["select_values"] = self._sync_property_select_values()

        if sync_default_units:
            summary["default_units"] = self._sync_default_unit_configurators()

        return summary

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------
    def _preflight_check(self) -> None:
        """Ensure the mapping sync is safe to execute."""
        if self.source_sales_channel == self.target_sales_channel:
            raise PreFlightCheckError("Source and target channels must differ.")

        if (
            self.source_sales_channel.multi_tenant_company_id
            != self.target_sales_channel.multi_tenant_company_id
        ):
            raise PreFlightCheckError(
                "Sales channels must belong to the same multi-tenant company."
            )

    # ------------------------------------------------------------------
    # Product type sync
    # ------------------------------------------------------------------
    def _sync_product_types(self) -> int:
        """Copy rule mappings based on product_type_code."""
        source_types = (
            AmazonProductType.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
                product_type_code__isnull=False,
            )
            .select_related("local_instance")
        )
        source_map: Dict[str, object] = {
            product_type.product_type_code: product_type.local_instance
            for product_type in source_types
        }

        if not source_map:
            return 0

        targets = list(
            AmazonProductType.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                product_type_code__in=source_map.keys(),
            )
            .select_related("local_instance")
        )

        updated = 0
        for target in targets:
            local_rule = source_map.get(target.product_type_code)
            if not local_rule or target.local_instance_id == local_rule.id:
                continue

            target.local_instance = local_rule
            target.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Default unit configurator sync
    # ------------------------------------------------------------------
    def _sync_default_unit_configurators(self) -> int:
        """Copy default unit selections by code + marketplace region."""
        source_configs = (
            AmazonDefaultUnitConfigurator.objects.filter(
                sales_channel=self.source_sales_channel,
                selected_unit__isnull=False,
                marketplace__api_region_code__isnull=False,
            )
            .select_related("marketplace")
        )

        source_map: Dict[Tuple[str, str], str] = {}
        for config in source_configs:
            if not config.code or not config.marketplace.api_region_code:
                continue
            source_map[
                (config.marketplace.api_region_code, config.code)
            ] = config.selected_unit

        if not source_map:
            return 0

        targets = (
            AmazonDefaultUnitConfigurator.objects.filter(
                sales_channel=self.target_sales_channel,
                selected_unit__isnull=True,
                marketplace__api_region_code__in={
                    key[0] for key in source_map.keys()
                },
            )
            .select_related("marketplace")
        )

        updated = 0
        for config in targets:
            region = config.marketplace.api_region_code
            if not (region and config.code):
                continue

            selected_unit = source_map.get((region, config.code))
            if not selected_unit:
                continue

            config.selected_unit = selected_unit
            config.save(update_fields=["selected_unit"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Property sync
    # ------------------------------------------------------------------
    def _sync_properties(self) -> int:
        """Copy property mappings strictly by code."""
        source_properties = (
            AmazonProperty.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
            )
            .select_related("local_instance")
        )

        code_map: Dict[str, object] = {}
        for prop in source_properties:
            if prop.code:
                code_map[prop.code] = prop.local_instance

        if not code_map:
            return 0

        targets = list(
            AmazonProperty.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
            )
        )

        updated = 0
        for prop in targets:
            if not prop.code:
                continue

            local_property = code_map.get(prop.code)

            if not local_property or prop.local_instance_id == getattr(local_property, "id", None):
                continue

            prop.local_instance = local_property
            prop.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Property select value sync
    # ------------------------------------------------------------------
    def _sync_property_select_values(self) -> int:
        """Copy select-value mappings using remote_value + property + region."""
        source_values = (
            AmazonPropertySelectValue.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
                amazon_property__local_instance__isnull=False,
                marketplace__api_region_code__isnull=False,
            )
            .select_related("amazon_property__local_instance", "marketplace")
        )

        total_updated = 0
        chunk: list[AmazonPropertySelectValue] = []

        for value in source_values.iterator(chunk_size=self.BATCH_SIZE):
            chunk.append(value)
            if len(chunk) >= self.BATCH_SIZE:
                total_updated += self._process_select_value_chunk(chunk)
                chunk = []

        if chunk:
            total_updated += self._process_select_value_chunk(chunk)

        return total_updated

    def _process_select_value_chunk(
        self, chunk: list[AmazonPropertySelectValue]
    ) -> int:
        """Process a subset of remote select values to limit memory usage."""
        chunk_map: Dict[Tuple[str, int, str], object] = {}
        property_ids: set[int] = set()
        remote_values: set[str] = set()
        region_codes: set[str] = set()

        for value in chunk:
            remote_value = value.remote_value
            local_property = value.amazon_property.local_instance
            marketplace_code = value.marketplace.api_region_code

            if not (remote_value and local_property and marketplace_code):
                continue

            key = (remote_value, local_property.id, marketplace_code)
            chunk_map[key] = value.local_instance
            property_ids.add(local_property.id)
            remote_values.add(remote_value)
            region_codes.add(marketplace_code)

        if not chunk_map:
            return 0

        targets = (
            AmazonPropertySelectValue.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                amazon_property__local_instance_id__in=property_ids,
                remote_value__in=remote_values,
                marketplace__api_region_code__in=region_codes,
            )
            .select_related("amazon_property__local_instance", "marketplace")
            .iterator(chunk_size=self.BATCH_SIZE)
        )

        updated = 0
        for value in targets:
            local_property = value.amazon_property.local_instance
            marketplace = value.marketplace
            remote_value = value.remote_value

            if not (
                remote_value and local_property and marketplace and marketplace.api_region_code
            ):
                continue

            key = (remote_value, local_property.id, marketplace.api_region_code)
            local_select_value = chunk_map.get(key)

            if not local_select_value or value.local_instance_id == getattr(
                local_select_value, "id", None
            ):
                continue

            value.local_instance = local_select_value
            value.save(update_fields=["local_instance"])
            updated += 1

        return updated
