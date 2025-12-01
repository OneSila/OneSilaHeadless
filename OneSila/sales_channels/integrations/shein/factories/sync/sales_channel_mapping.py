from __future__ import annotations

from typing import Dict, Tuple

from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductType,
    SheinProperty,
    SheinPropertySelectValue,
)
from sales_channels.integrations.shein.models.sales_channels import SheinSalesChannel


class SheinSalesChannelMappingSyncFactory:
    """Copy Shein mapping metadata from one sales channel to another."""

    BATCH_SIZE = 25000

    def __init__(
        self,
        *,
        source_sales_channel: SheinSalesChannel,
        target_sales_channel: SheinSalesChannel,
    ) -> None:
        self.source_sales_channel = source_sales_channel
        self.target_sales_channel = target_sales_channel

    def run(
        self,
        *,
        sync_product_types: bool = True,
        sync_properties: bool = True,
        sync_select_values: bool = True,
        sync_internal_properties: bool = True,
        sync_internal_property_options: bool = True,
    ) -> Dict[str, int]:
        """Execute the sync for the enabled data sets."""
        self._preflight_check()

        summary = {
            "product_types": 0,
            "properties": 0,
            "select_values": 0,
            "internal_properties": 0,
            "internal_property_options": 0,
        }

        if sync_product_types:
            summary["product_types"] = self._sync_product_types()

        if sync_properties:
            summary["properties"] = self._sync_properties()

        if sync_select_values:
            summary["select_values"] = self._sync_property_select_values()

        if sync_internal_properties:
            summary["internal_properties"] = self._sync_internal_properties()

        if sync_internal_property_options:
            summary["internal_property_options"] = (
                self._sync_internal_property_options()
            )

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
        """Copy product type mappings based on remote_id."""
        source_types = (
            SheinProductType.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .select_related("local_instance")
        )

        source_map: Dict[str, object] = {
            product_type.remote_id: product_type.local_instance
            for product_type in source_types
            if product_type.remote_id
        }

        if not source_map:
            return 0

        targets = list(
            SheinProductType.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                remote_id__in=source_map.keys(),
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .select_related("local_instance")
        )

        updated = 0
        for target in targets:
            local_rule = source_map.get(target.remote_id)
            if not local_rule or target.local_instance_id == getattr(
                local_rule, "id", None
            ):
                continue

            target.local_instance = local_rule
            target.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Property sync
    # ------------------------------------------------------------------
    def _sync_properties(self) -> int:
        """Copy property mappings strictly by remote_id."""
        source_properties = (
            SheinProperty.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .select_related("local_instance")
        )

        remote_map: Dict[str, object] = {
            prop.remote_id: prop.local_instance
            for prop in source_properties
            if prop.remote_id
        }

        if not remote_map:
            return 0

        targets = list(
            SheinProperty.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                remote_id__in=remote_map.keys(),
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
        )

        updated = 0
        for prop in targets:
            local_property = remote_map.get(prop.remote_id)

            if not local_property or prop.local_instance_id == getattr(
                local_property, "id", None
            ):
                continue

            prop.local_instance = local_property
            prop.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Property select value sync
    # ------------------------------------------------------------------
    def _sync_property_select_values(self) -> int:
        """Copy select-value mappings using remote_id + property."""
        source_values = (
            SheinPropertySelectValue.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
                remote_property__local_instance__isnull=False,
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .exclude(remote_property__remote_id__isnull=True)
            .exclude(remote_property__remote_id="")
            .select_related("remote_property__local_instance")
        )

        total_updated = 0
        chunk: list[SheinPropertySelectValue] = []

        for value in source_values.iterator(chunk_size=self.BATCH_SIZE):
            chunk.append(value)
            if len(chunk) >= self.BATCH_SIZE:
                total_updated += self._process_select_value_chunk(chunk)
                chunk = []

        if chunk:
            total_updated += self._process_select_value_chunk(chunk)

        return total_updated

    def _process_select_value_chunk(
        self, chunk: list[SheinPropertySelectValue]
    ) -> int:
        """Process a subset of remote select values to limit memory usage."""
        chunk_map: Dict[Tuple[str, int], object] = {}
        property_ids: set[int] = set()
        remote_ids: set[str] = set()

        for value in chunk:
            remote_id = value.remote_id
            remote_property = value.remote_property
            local_property = getattr(remote_property, "local_instance", None)

            if not (remote_id and remote_property and local_property):
                continue

            key = (remote_id, local_property.id)
            chunk_map[key] = value.local_instance
            property_ids.add(local_property.id)
            remote_ids.add(remote_id)

        if not chunk_map:
            return 0

        targets = (
            SheinPropertySelectValue.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                remote_property__local_instance_id__in=property_ids,
                remote_id__in=remote_ids,
            )
            .select_related("remote_property__local_instance")
            .iterator(chunk_size=self.BATCH_SIZE)
        )

        updated = 0
        for value in targets:
            local_property = getattr(value.remote_property, "local_instance", None)
            remote_id = value.remote_id

            if not (local_property and remote_id):
                continue

            key = (remote_id, local_property.id)
            local_select_value = chunk_map.get(key)

            if not local_select_value or value.local_instance_id == getattr(
                local_select_value, "id", None
            ):
                continue

            value.local_instance = local_select_value
            value.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Internal property sync
    # ------------------------------------------------------------------
    def _sync_internal_properties(self) -> int:
        """Copy internal property mappings by code."""
        source_internal_properties = (
            SheinInternalProperty.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
            )
            .exclude(code__isnull=True)
            .exclude(code="")
            .select_related("local_instance")
        )

        code_map: Dict[str, object] = {
            internal_property.code: internal_property.local_instance
            for internal_property in source_internal_properties
            if internal_property.code
        }

        if not code_map:
            return 0

        targets = list(
            SheinInternalProperty.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                code__in=code_map.keys(),
            )
            .exclude(code__isnull=True)
            .exclude(code="")
        )

        updated = 0
        for internal_property in targets:
            local_property = code_map.get(internal_property.code)

            if not local_property or internal_property.local_instance_id == getattr(
                local_property, "id", None
            ):
                continue

            internal_property.local_instance = local_property
            internal_property.save(update_fields=["local_instance"])
            updated += 1

        return updated

    # ------------------------------------------------------------------
    # Internal property options sync
    # ------------------------------------------------------------------
    def _sync_internal_property_options(self) -> int:
        """Copy internal property option mappings by internal_property + value."""
        source_options = (
            SheinInternalPropertyOption.objects.filter(
                sales_channel=self.source_sales_channel,
                local_instance__isnull=False,
                internal_property__code__isnull=False,
            )
            .exclude(internal_property__code="")
            .exclude(value="")
            .select_related("internal_property")
        )

        option_map: Dict[Tuple[str, str], object] = {}
        internal_property_codes: set[str] = set()
        values: set[str] = set()

        for option in source_options:
            code = getattr(option.internal_property, "code", None)
            value = option.value
            if not (code and value):
                continue

            key = (code, value)
            option_map[key] = option.local_instance
            internal_property_codes.add(code)
            values.add(value)

        if not option_map:
            return 0

        targets = (
            SheinInternalPropertyOption.objects.filter(
                sales_channel=self.target_sales_channel,
                local_instance__isnull=True,
                internal_property__code__in=internal_property_codes,
                value__in=values,
            )
            .select_related("internal_property")
            .iterator(chunk_size=self.BATCH_SIZE)
        )

        updated = 0
        for option in targets:
            code = getattr(option.internal_property, "code", None)
            value = option.value

            if not (code and value):
                continue

            key = (code, value)
            local_option_value = option_map.get(key)

            if not local_option_value or option.local_instance_id == getattr(
                local_option_value, "id", None
            ):
                continue

            option.local_instance = local_option_value
            option.save(update_fields=["local_instance"])
            updated += 1

        return updated
