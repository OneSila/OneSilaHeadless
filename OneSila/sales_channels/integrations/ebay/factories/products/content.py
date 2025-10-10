from __future__ import annotations

from typing import Any

from ebay_rest.api.sell_inventory.rest import ApiException
from ebay_rest.error import Error as EbayApiError

from sales_channels.factories.products.content import RemoteProductContentUpdateFactory

from sales_channels.integrations.ebay.exceptions import EbayResponseException
from sales_channels.integrations.ebay.models.products import EbayProductContent

from .mixins import EbayInventoryItemPushMixin, _extract_ebay_api_error_message


class EbayProductContentUpdateFactory(
    EbayInventoryItemPushMixin,
    RemoteProductContentUpdateFactory,
):
    """Push content updates to eBay using full inventory payloads."""

    remote_model_class = EbayProductContent

    def __init__(
        self,
        *args: Any,
        view,
        get_value_only: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, view=view, get_value_only=get_value_only, **kwargs)

    def update_remote(self) -> Any:
        response = self.send_inventory_payload()

        if not self.get_value_only:
            self._update_listing_description()

        return response

    def get_remote_instance(self):  # pragma: no cover - base class expects override
        return self.remote_instance

    def _update_listing_description(self) -> None:
        description = self.get_listing_description()
        if not description:
            return

        offer_id = self._get_offer_remote_id()
        if not offer_id:
            return

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        payload = {"listingDescription": description}
        self._log_api_payload(action="update_offer", payload=payload)
        try:
            api.sell_inventory_update_offer(
                offer_id=offer_id,
                body=payload,
                content_language=self._get_content_language(),
                content_type="application/json",
            )
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc
