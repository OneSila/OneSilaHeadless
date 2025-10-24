"""Factories pulling and normalising Shein marketplace metadata."""

from collections.abc import Iterable
from typing import Dict, Optional

from currencies.models import Currency
from django.db import transaction

from sales_channels.factories.mixins import PullRemoteInstanceMixin

from sales_channels.integrations.shein.factories.mixins import SheinSiteListMixin
from sales_channels.integrations.shein.models import (
    SheinRemoteCurrency,
    SheinRemoteMarketplace,
    SheinSalesChannelView,
)


class SheinMarketplacePullFactory(SheinSiteListMixin, PullRemoteInstanceMixin):
    """Pull Shein storefront data into marketplace, view, and currency mirrors."""

    remote_model_class = SheinRemoteMarketplace
    field_mapping = {
        "remote_id": "site_abbr",
        "name": "site_name",
        "is_default": "is_default",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_id"]

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def __init__(self, *, sales_channel):
        self._local_currencies: Dict[str, Currency] = {}
        super().__init__(sales_channel, api=None)

    def get_api(self):
        """Required by ``PullRemoteInstanceMixin`` but unused for Shein."""

        return None

    def allow_process(self, remote_data):
        return bool(remote_data.get("site_abbr"))

    def fetch_remote_instances(self):
        channel_domain = self.get_channel_domain()
        remote_instances: list[dict] = []
        default_remote_id: Optional[str] = None
        currency_codes: set[str] = set()

        for _, sub_site in self._iterate_sub_sites():
            site_abbr = sub_site.get("site_abbr")
            site_name = sub_site.get("site_name")

            if not site_abbr or not site_name:
                continue

            domain = self.derive_domain_from_site_abbr(site_abbr)
            url = self.build_view_url(domain)

            if (
                channel_domain
                and domain
                and (
                    channel_domain == domain
                    or channel_domain.endswith(f".{domain}")
                )
            ):
                default_remote_id = default_remote_id or site_abbr

            currency = (sub_site.get("currency") or "").strip() or None
            if currency:
                currency_codes.add(currency)

            remote_instances.append(
                {
                    "site_abbr": site_abbr,
                    "site_name": site_name,
                    "site_status": sub_site.get("site_status"),
                    "store_type": sub_site.get("store_type"),
                    "domain": domain,
                    "url": url,
                    "currency": currency,
                    "symbol_left": sub_site.get("symbol_left"),
                    "symbol_right": sub_site.get("symbol_right"),
                    "is_default": False,
                }
            )

        if not remote_instances:
            self.remote_instances = []
            self._local_currencies = {}
            return

        if default_remote_id is None:
            default_remote_id = remote_instances[0]["site_abbr"]

        for entry in remote_instances:
            entry["is_default"] = entry["site_abbr"] == default_remote_id

        self.remote_instances = remote_instances
        self._local_currencies = self._load_local_currencies(currency_codes)

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------
    def _iterate_sub_sites(self) -> Iterable[tuple[dict, dict]]:
        for marketplace in self.fetch_site_records():
            for sub_site in marketplace.get("sub_site_list", []):
                yield marketplace, sub_site

    def _load_local_currencies(self, codes: set[str]) -> Dict[str, Currency]:
        if not codes:
            return {}

        queryset = Currency.objects.filter(
            iso_code__in=codes,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
        return {currency.iso_code: currency for currency in queryset}

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        with transaction.atomic():
            view = self._sync_view(remote_instance_mirror, remote_data)
            self._sync_currency(remote_data)

    def _sync_view(self, marketplace: SheinRemoteMarketplace, data: dict) -> SheinSalesChannelView:
        defaults = {
            "name": data.get("site_name"),
            "url": data.get("url"),
            "site_status": data.get("site_status"),
            "store_type": data.get("store_type"),
            "is_default": data.get("is_default", False),
            "marketplace": marketplace,
            "multi_tenant_company": self.sales_channel.multi_tenant_company,
        }

        view, _ = SheinSalesChannelView.objects.update_or_create(
            sales_channel=self.sales_channel,
            remote_id=data["site_abbr"],
            defaults=defaults,
        )

        if defaults["is_default"]:
            (
                SheinSalesChannelView.objects
                .filter(sales_channel=self.sales_channel)
                .exclude(pk=view.pk)
                .update(is_default=False)
            )

        return view

    def _sync_currency(self, data: dict) -> None:
        code = data.get("currency")
        if not code:
            return

        defaults = {
            "remote_id": code,
            "symbol_left": data.get("symbol_left"),
            "symbol_right": data.get("symbol_right"),
            "local_instance": self._local_currencies.get(code),
        }

        SheinRemoteCurrency.objects.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_code=code,
            defaults=defaults,
        )
