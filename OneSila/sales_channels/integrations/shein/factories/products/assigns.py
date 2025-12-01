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

        default_assign = next(
            (assign for assign in assigns if getattr(assign.sales_channel_view, "is_default", False)),
            None,
        ) or assigns[0]

        main_site = getattr(default_assign.sales_channel_view, "remote_id", None)
        sub_sites: List[str] = []

        for assign in assigns:
            view_remote_id = getattr(assign.sales_channel_view, "remote_id", None)
            if not view_remote_id or assign == default_assign:
                continue
            sub_sites.append(view_remote_id)

        site_entry = {
            "main_site": main_site,
            "sub_site_list": sub_sites,
        }
        return [site_entry]
