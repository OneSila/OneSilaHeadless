from typing import Any

from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.factories.products.assigns import SheinSalesChannelAssignFactoryMixin
from sales_channels.integrations.shein.models import SheinProduct
from sales_channels.models.products import RemoteProduct


class SheinProductShelfUpdateFactory(SheinSignatureMixin, SheinSalesChannelAssignFactoryMixin):
    """Publish/unpublish SKCs for a Shein product."""

    modify_skc_shelf_path = "/open-api/goods/modify-skc-shelf"

    def __init__(
        self,
        *,
        sales_channel,
        remote_product,
        shelf_state: int = 1,
    ) -> None:
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self.shelf_state = shelf_state
        self.local_instance = getattr(remote_product, "local_instance", None)

    def validate(self) -> None:
        if self.remote_product is None:
            raise PreFlightCheckError("Missing remote product for Shein shelf update.")
        if self.shelf_state not in (1, 2):
            raise PreFlightCheckError("Shein shelf_state must be 1 (publish) or 2 (unpublish).")
        status = getattr(self.remote_product, "status", None)
        if status != RemoteProduct.STATUS_COMPLETED:
            raise PreFlightCheckError("Shein shelf updates require the remote product to be completed.")

    def _collect_site_list(self) -> list[str]:
        site_entries = self.build_site_list(product=self.local_instance) if self.local_instance else []
        sites: list[str] = []
        for entry in site_entries:
            sub_sites = entry.get("sub_site_list") if isinstance(entry, dict) else None
            if isinstance(sub_sites, list):
                for site in sub_sites:
                    value = str(site).strip()
                    if value and value not in sites:
                        sites.append(value)
        return sites

    def _collect_skc_names(self) -> list[str]:
        skc_names: list[str] = []

        if getattr(self.remote_product, "is_variation", False):
            value = str(getattr(self.remote_product, "skc_name", "") or "").strip()
            if value:
                skc_names.append(value)
            return skc_names

        if self.local_instance is not None and self.local_instance.is_configurable():
            children = SheinProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=self.remote_product,
            ).exclude(skc_name__isnull=True).exclude(skc_name="")
            for skc_name in children.values_list("skc_name", flat=True):
                value = str(skc_name or "").strip()
                if value and value not in skc_names:
                    skc_names.append(value)

        if not skc_names:
            value = str(getattr(self.remote_product, "skc_name", "") or "").strip()
            if value:
                skc_names.append(value)

        return skc_names

    def build_payload(self) -> dict[str, Any]:
        site_list = self._collect_site_list()
        if not site_list:
            raise PreFlightCheckError("Missing Shein site_list for shelf update.")

        skc_names = self._collect_skc_names()
        if not skc_names:
            raise PreFlightCheckError("Missing skc_name for Shein shelf update.")

        skc_site_info_list = [
            {
                "skc_name": skc_name,
                "shelf_state": self.shelf_state,
                "site_list": site_list,
            }
            for skc_name in skc_names
        ]
        return {"skc_site_info_list": skc_site_info_list}

    def fetch(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.shein_post(path=self.modify_skc_shelf_path, payload=payload)
        response_data = response.json() if hasattr(response, "json") else {}
        return response_data if isinstance(response_data, dict) else {"response": response_data}

    def run(self) -> dict[str, Any]:
        self.validate()
        payload = self.build_payload()
        return self.fetch(payload=payload)
