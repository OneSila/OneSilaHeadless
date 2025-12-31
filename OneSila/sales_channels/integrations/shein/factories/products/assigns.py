from __future__ import annotations

from typing import Dict, List

from sales_channels.models import SalesChannelViewAssign


class SheinSalesChannelAssignFactoryMixin:
    """Build Shein site_list payloads from product view assignments."""

    def build_site_list(self, *, product) -> List[Dict[str, object]]:
        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=product,
            ).select_related("sales_channel_view")
        )
        if not assigns:
            return []

        sub_sites: List[str] = []
        for assign in assigns:
            view_remote_id = getattr(assign.sales_channel_view, "remote_id", None)
            if not view_remote_id:
                continue
            value = str(view_remote_id).strip()
            if not value or value in sub_sites:
                continue
            sub_sites.append(value)

        if not sub_sites:
            return []

        return [
            {
                "main_site": "shein",
                "sub_site_list": sub_sites,
            }
        ]
