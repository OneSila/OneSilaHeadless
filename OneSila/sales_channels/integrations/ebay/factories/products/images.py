from __future__ import annotations

from typing import Any

from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughDeleteFactory,
    RemoteMediaProductThroughUpdateFactory,
)

from sales_channels.integrations.ebay.models.products import EbayMediaThroughProduct

from .mixins import EbayInventoryItemPushMixin


class EbayMediaProductThroughBase(EbayInventoryItemPushMixin):
    """Shared behaviour for eBay image assignments."""

    remote_model_class = EbayMediaThroughProduct

    def __init__(
        self,
        *args: Any,
        view,
        get_value_only: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, view=view, get_value_only=get_value_only, **kwargs)

    def customize_remote_instance_data(self) -> dict[str, Any]:
        self.remote_instance_data["remote_product"] = self.remote_product
        return self.remote_instance_data


class EbayMediaProductThroughCreateFactory(
    EbayMediaProductThroughBase,
    RemoteMediaProductThroughCreateFactory,
):
    def create_remote(self) -> Any:
        return self.send_inventory_payload()


class EbayMediaProductThroughUpdateFactory(
    EbayMediaProductThroughBase,
    RemoteMediaProductThroughUpdateFactory,
):
    create_factory_class = EbayMediaProductThroughCreateFactory

    def update_remote(self) -> Any:
        return self.send_inventory_payload()

    def needs_update(self) -> bool:
        return True


class EbayMediaProductThroughDeleteFactory(
    EbayMediaProductThroughBase,
    RemoteMediaProductThroughDeleteFactory,
):
    delete_remote_instance = True

    def delete_remote(self) -> Any:
        return self.send_inventory_payload()
