from __future__ import annotations

from typing import Any, Dict

from sales_channels.factories.products.assigns import RemoteSalesChannelViewAssignUpdateFactory
from sales_channels.integrations.ebay.factories.helpers import (
    normalize_ebay_response,
    resolve_ebay_view,
)
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.factories.products.mixins import EbayInventoryItemPushMixin
from sales_channels.integrations.ebay.models.products import EbayProduct
from sales_channels.models import SalesChannelViewAssign

class _HelperBase:
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple passthrough
        pass


class _EbayAssignOfferHelper(EbayInventoryItemPushMixin, _HelperBase):
    """Thin wrapper around offer endpoints for assign operations."""

    def __init__(
        self,
        *,
        sales_channel,
        remote_product,
        view,
        api=None,
    ) -> None:
        self.sales_channel = sales_channel
        resolved_view = resolve_ebay_view(view)
        if resolved_view is None:
            raise ValueError("Ebay assign factories require a concrete sales channel view")
        self.view = resolved_view
        self.remote_product = remote_product
        self.remote_instance = remote_product
        self.local_instance = getattr(remote_product, "local_instance", None)
        if self.local_instance is None:
            raise ValueError("Remote product missing local instance")
        if api is not None:
            self.api = api
        super().__init__(
            sales_channel=sales_channel,
            local_instance=self.local_instance,
            view=self.view,
        )


class EbaySalesChannelAssignFactoryMixin(GetEbayAPIMixin):
    """Shared helpers for eBay assign update/delete factories."""

    remote_model_class = EbayProduct

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        view,
        api=None,
    ) -> None:
        resolved_view = resolve_ebay_view(view)
        if resolved_view is None:
            raise ValueError("Ebay assign factories require a concrete sales channel view")
        self.view = resolved_view
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            api=api,
        )
        self.remote_product = self.remote_instance

    def build_payload(self) -> Dict[str, Any]:
        self.payload = {"view_id": getattr(self.view, "id", None)}
        return self.payload

    def serialize_response(self, response: Any) -> Any:
        return normalize_ebay_response(response)

    def preflight_process(self) -> None:
        if getattr(self.view, "sales_channel_id", None) != getattr(self.sales_channel, "id", None):
            raise ValueError("View does not belong to the provided sales channel")
        if self.remote_instance is None:
            raise ValueError("Remote product not found for assign operation")

    def _build_offer_helper(self, *, remote_product: EbayProduct) -> _EbayAssignOfferHelper:
        return _EbayAssignOfferHelper(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            view=self.view,
            api=getattr(self, "api", None),
        )

    def _get_remote_children(self, *, parent: EbayProduct) -> list[EbayProduct]:
        return list(
            EbayProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=parent,
            ).select_related("local_instance")
        )

    def _sync_assign_remote_product(self) -> None:
        if self.remote_instance is None:
            return
        assigns = SalesChannelViewAssign.objects.filter(
            product=self.local_instance,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
        )
        for assign in assigns:
            updates: list[str] = []
            if assign.remote_product_id != self.remote_instance.id:
                assign.remote_product = self.remote_instance
                updates.append("remote_product")
            if assign.sales_channel_id != self.sales_channel.id:
                assign.sales_channel = self.sales_channel
                updates.append("sales_channel")
            if updates:
                assign.save(update_fields=updates)


class EbaySalesChannelViewAssignUpdateFactory(
    EbaySalesChannelAssignFactoryMixin,
    RemoteSalesChannelViewAssignUpdateFactory,
):
    """Ensure offers exist for a product when a new view assign is created."""

    def needs_update(self) -> bool:
        return True

    def update_remote(self) -> Dict[str, Any]:
        remote_product = self.remote_instance
        if remote_product is None:
            raise ValueError("Remote product not resolved for assign update")

        self._sync_assign_remote_product()
        helper = self._build_offer_helper(remote_product=remote_product)
        child_remotes = self._get_remote_children(parent=remote_product)

        if child_remotes:
            child_responses: list[Dict[str, Any]] = []
            for child_remote in child_remotes:
                child_helper = self._build_offer_helper(remote_product=child_remote)
                offer_response = child_helper.send_offer()
                child_responses.append(
                    {
                        "remote_product_id": child_remote.id,
                        "offer": normalize_ebay_response(offer_response),
                    }
                )
            publish_response = helper.publish_group()
            return {
                "view_id": getattr(self.view, "id", None),
                "children": child_responses,
                "publish": normalize_ebay_response(publish_response),
            }

        offer_response = helper.send_offer()
        publish_response = helper.publish_offer()
        return {
            "view_id": getattr(self.view, "id", None),
            "offer": normalize_ebay_response(offer_response),
            "publish": normalize_ebay_response(publish_response),
        }


class EbaySalesChannelViewAssignDeleteFactory(
    EbaySalesChannelAssignFactoryMixin,
    RemoteSalesChannelViewAssignUpdateFactory,
):
    """Withdraw and delete offers for a view assign removal without touching inventory."""

    def needs_update(self) -> bool:
        return True

    def update_remote(self) -> Dict[str, Any]:
        remote_product = self.remote_instance
        if remote_product is None:
            raise ValueError("Remote product not resolved for assign delete")

        helper = self._build_offer_helper(remote_product=remote_product)
        child_remotes = self._get_remote_children(parent=remote_product)

        if child_remotes:
            withdraw_group = helper.withdraw_group()
            offer_responses: list[Dict[str, Any]] = []
            for target in [remote_product, *child_remotes]:
                target_helper = helper if target is remote_product else self._build_offer_helper(remote_product=target)
                withdraw_response = target_helper.withdraw_offer()
                delete_response = target_helper.delete_offer()
                offer_responses.append(
                    {
                        "remote_product_id": target.id,
                        "withdraw": normalize_ebay_response(withdraw_response),
                        "delete": normalize_ebay_response(delete_response),
                    }
                )
            return {
                "view_id": getattr(self.view, "id", None),
                "withdraw_group": normalize_ebay_response(withdraw_group),
                "offers": offer_responses,
            }

        withdraw_response = helper.withdraw_offer()
        delete_response = helper.delete_offer()
        return {
            "view_id": getattr(self.view, "id", None),
            "withdraw": normalize_ebay_response(withdraw_response),
            "delete": normalize_ebay_response(delete_response),
        }
