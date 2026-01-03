"""Factories handling Shein storefront metadata."""

from typing import Any, Optional

from sales_channels.factories.mixins import PullRemoteInstanceMixin
from currencies.models import Currency

from sales_channels.integrations.shein.factories.mixins import SheinSiteListMixin
from sales_channels.integrations.shein.models import (
    SheinSalesChannelView,
    SheinRemoteCurrency,
)


class SheinSalesChannelViewPullFactory(SheinSiteListMixin, PullRemoteInstanceMixin):
    """Pull Shein storefronts (sub-sites) and mirror them locally."""

    remote_model_class = SheinSalesChannelView
    field_mapping = {
        "remote_id": "remote_id",
        "name": "site_name",
        "site_status": "site_status",
        "store_type": "store_type",
        "url": "url",
        "is_default": "is_default",
        "merchant_location_key": "merchant_location_key",
        "merchant_location_choices": "merchant_location_choices",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_id"]

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def __init__(self, *, sales_channel):
        super().__init__(sales_channel, api=None)

    def get_api(self):
        return None

    def allow_process(self, remote_data):
        return bool(remote_data.get("site_abbr"))

    def fetch_remote_instances(self):
        records = self.fetch_site_records()
        warehouse_key, warehouse_choices = self._sync_warehouses()
        channel_domain = self.get_channel_domain()

        remote_instances: list[dict] = []
        default_remote_id: str | None = None

        for marketplace in records:
            for sub_site in marketplace.get("sub_site_list", []):
                site_abbr = sub_site.get("site_abbr")
                if not site_abbr:
                    continue

                domain = sub_site.get("derived_domain") or self.derive_domain_from_site_abbr(site_abbr)
                url = self.build_view_url(domain)

                matches_channel = False
                if channel_domain and domain:
                    matches_channel = channel_domain == domain or channel_domain.endswith(f".{domain}")

                if matches_channel and default_remote_id is None:
                    default_remote_id = site_abbr

                remote_instances.append(
                    {
                        "remote_id": site_abbr,
                        "site_abbr": site_abbr,
                        "site_name": sub_site.get("site_name"),
                        "site_status": sub_site.get("site_status"),
                        "store_type": sub_site.get("store_type"),
                        "domain": domain,
                        "url": url,
                        "marketplace_remote_id": site_abbr,
                        "marketplace_is_default": marketplace.get("is_default"),
                        "currency": sub_site.get("currency"),
                        "symbol_left": sub_site.get("symbol_left"),
                        "symbol_right": sub_site.get("symbol_right"),
                        "is_default": False,
                        "merchant_location_key": warehouse_key,
                        "merchant_location_choices": warehouse_choices,
                    }
                )

        if not remote_instances:
            self.remote_instances = []
            return

        if default_remote_id is None:
            prioritized = [
                item["site_abbr"]
                for item in remote_instances
                if item.get("marketplace_is_default")
            ]
            if prioritized:
                default_remote_id = prioritized[0]
            else:
                default_remote_id = remote_instances[0]["site_abbr"]

        for item in remote_instances:
            item["is_default"] = item.get("site_abbr") == default_remote_id

        self.remote_instances = remote_instances

    def _sync_warehouses(self) -> tuple[Optional[str], list[dict[str, Any]]]:
        selected_key: Optional[str] = None
        choices: list[dict[str, Any]] = []

        try:
            response = self.shein_get(path="/open-api/msc/warehouse/list", payload={})
            data = response.json() if hasattr(response, "json") else {}
            info = data.get("info") if isinstance(data, dict) else {}
            warehouses = info.get("list") if isinstance(info, dict) else []
        except Exception:
            warehouses = []

        if isinstance(warehouses, list):
            for entry in warehouses:
                if not isinstance(entry, dict):
                    continue
                code = (entry.get("warehouseCode") or "").strip()
                if not code:
                    continue
                cleaned = {
                    "warehouseCode": code,
                    "warehouseName": entry.get("warehouseName"),
                    "saleCountryList": entry.get("saleCountryList") or [],
                    "createType": entry.get("createType"),
                    "warehouseType": entry.get("warehouseType"),
                    "authServiceCode": entry.get("authServiceCode"),
                    "authServiceName": entry.get("authServiceName"),
                }
                choices.append(cleaned)
                if selected_key is None:
                    selected_key = code

        return selected_key, choices

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        super().create_remote_instance_mirror(remote_data, remote_instance_mirror)
        remote_instance_mirror.raw_data = remote_data or {}
        remote_instance_mirror.save()
        self._sync_currency_for_view(remote_data=remote_data, view=remote_instance_mirror)

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        remote_instance_mirror.raw_data = remote_data or {}
        remote_instance_mirror.save()
        self._sync_currency_for_view(remote_data=remote_data, view=remote_instance_mirror)

    def _sync_currency_for_view(self, *, remote_data: Any, view: SheinSalesChannelView) -> None:
        if not isinstance(remote_data, dict):
            return

        remote_code = (remote_data.get("currency") or "").strip()
        if not remote_code:
            return

        local_currency = Currency.objects.filter(
            iso_code=remote_code,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        ).first()

        defaults = {
            "local_instance": local_currency,
            "symbol_left": remote_data.get("symbol_left") or "",
            "symbol_right": remote_data.get("symbol_right") or "",
        }

        SheinRemoteCurrency._base_manager.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=view,
            defaults={**defaults, "remote_code": remote_code},
        )
