from __future__ import annotations

from typing import Any, Dict, List

from sales_channels.factories.products.assigns import RemoteSalesChannelViewAssignUpdateFactory
from sales_channels.integrations.shein.models import SheinProduct
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


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


class SheinSalesChannelViewAssignUpdateFactory(
    SheinSalesChannelAssignFactoryMixin,
    RemoteSalesChannelViewAssignUpdateFactory,
):
    """Sync Shein SKC site availability after a view assignment changes."""

    remote_model_class = SheinProduct

    def __init__(
        self,
        sales_channel,
        local_instance,
        api=None,
        *,
        view=None,
        is_delete: bool = False,
    ):
        self.view = view
        self.is_delete = bool(is_delete)
        self.sales_channel_assigns = SalesChannelViewAssign.objects.none()
        super().__init__(sales_channel=sales_channel, local_instance=local_instance, api=api)

    def get_remote_instance(self):
        self.remote_instance = (
            self.remote_model_class.objects.filter(
                sales_channel=self.sales_channel,
                local_instance=self.local_instance,
                is_variation=False,
            )
            .order_by("id")
            .first()
        )
        return self.remote_instance

    def fetch_sales_channels_assign(self):
        self.sales_channel_assigns = SalesChannelViewAssign.objects.filter(
            sales_channel=self.sales_channel,
            product=self.local_instance,
            sales_channel__active=True,
        ).select_related("sales_channel_view", "remote_product")

    def _normalize_assign_statuses(self):
        pending_status = SalesChannelViewAssign.STATUS_PENDING_CREATION
        created_status = SalesChannelViewAssign.STATUS_CREATED

        pending_assigns = self.sales_channel_assigns.filter(status=pending_status)
        if pending_assigns.exists():
            pending_assigns.update(status=created_status)

    def add_to_remote_product_if_needed(self):
        if self.remote_instance is None:
            return

        for assign in self.sales_channel_assigns:
            update_fields: list[str] = []
            if assign.remote_product_id != self.remote_instance.id:
                assign.remote_product = self.remote_instance
                update_fields.append("remote_product")
            if assign.status != SalesChannelViewAssign.STATUS_CREATED:
                assign.status = SalesChannelViewAssign.STATUS_CREATED
                update_fields.append("status")
            if update_fields:
                assign.save(update_fields=update_fields)

    def _resolve_view_site_code(self) -> str | None:
        remote_id = getattr(self.view, "remote_id", None)
        value = str(remote_id or "").strip()
        return value or None

    def _publish_current_assignments(self) -> dict[str, Any]:
        from sales_channels.integrations.shein.factories.products.shelf import (
            SheinProductShelfUpdateFactory,
        )

        return SheinProductShelfUpdateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_instance,
            shelf_state=1,
        ).run()

    def _unpublish_removed_assignment(self) -> dict[str, Any] | None:
        from sales_channels.integrations.shein.factories.products.shelf import (
            SheinProductShelfUpdateFactory,
        )

        removed_site = self._resolve_view_site_code()
        if not removed_site:
            return None

        return SheinProductShelfUpdateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_instance,
            shelf_state=2,
            site_list=[removed_site],
        ).run()

    def update_remote(self):
        if self.remote_instance is None:
            return None

        if self.remote_instance.status != RemoteProduct.STATUS_COMPLETED:
            return None

        if self.is_delete:
            return self._unpublish_removed_assignment()

        return self._publish_current_assignments()

    def serialize_response(self, response):
        return response

    def run(self):
        self.fetch_sales_channels_assign()
        self._normalize_assign_statuses()
        self.add_to_remote_product_if_needed()
        return self.update_remote()
