"""Factories handling Shein storefront metadata."""

from sales_channels.factories.mixins import PullRemoteInstanceMixin

from sales_channels.integrations.shein.factories.mixins import SheinSiteListMixin
from sales_channels.integrations.shein.models import (
    SheinRemoteMarketplace,
    SheinSalesChannelView,
)


class SheinSalesChannelViewPullFactory(SheinSiteListMixin, PullRemoteInstanceMixin):
    """Pull Shein storefronts (sub-sites) and mirror them locally."""

    remote_model_class = SheinSalesChannelView
    field_mapping = {
        "remote_id": "site_abbr",
        "name": "site_name",
        "site_status": "site_status",
        "store_type": "store_type",
        "url": "url",
        "is_default": "is_default",
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
        channel_domain = self.get_channel_domain()

        remote_instances: list[dict] = []
        default_remote_id: str | None = None

        for marketplace in records:
            marketplace_remote_id = marketplace.get("main_site")
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
                        "site_abbr": site_abbr,
                        "site_name": sub_site.get("site_name"),
                        "site_status": sub_site.get("site_status"),
                        "store_type": sub_site.get("store_type"),
                        "domain": domain,
                        "url": url,
                        "marketplace_remote_id": marketplace_remote_id,
                        "marketplace_is_default": marketplace.get("is_default"),
                        "currency": sub_site.get("currency"),
                        "symbol_left": sub_site.get("symbol_left"),
                        "symbol_right": sub_site.get("symbol_right"),
                        "is_default": False,
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

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        marketplace_remote_id = remote_data.get("marketplace_remote_id")
        marketplace = None

        if marketplace_remote_id:
            marketplace = SheinRemoteMarketplace.objects.filter(
                sales_channel=self.sales_channel,
                remote_id=marketplace_remote_id,
            ).first()

        if remote_instance_mirror.marketplace_id != (marketplace.id if marketplace else None):
            remote_instance_mirror.marketplace = marketplace

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        super().create_remote_instance_mirror(remote_data, remote_instance_mirror)
        self.add_fields_to_remote_instance_mirror(remote_data, remote_instance_mirror)
        remote_instance_mirror.save()
