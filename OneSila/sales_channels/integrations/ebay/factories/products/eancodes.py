from __future__ import annotations

from typing import Any

from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.models.sales_channels import SalesChannelViewAssign

from sales_channels.integrations.ebay.factories.products.mixins import (
    EbayInventoryItemPushMixin,
    EbayInventoryItemPayloadMixin,
)
from sales_channels.integrations.ebay.models.products import EbayEanCode


class EbayEanCodeUpdateFactory(EbayInventoryItemPushMixin, RemoteEanCodeUpdateFactory):
    """Update eBay EAN/UPC identifiers by resubmitting the inventory item payload."""

    remote_model_class = EbayEanCode

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        remote_product,
        view,
        api: Any | None = None,
        skip_checks: bool = False,
        remote_instance=None,
        get_value_only: bool = False,
    ) -> None:
        self._ean_factory_marker = True
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_product=remote_product,
            api=api,
            skip_checks=skip_checks,
            remote_instance=remote_instance,
            view=view,
            get_value_only=get_value_only,
        )
        self._ean_value: str | None = None

    def preflight_check(self) -> bool:
        if self.skip_checks:
            return True

        if not self.remote_product or not getattr(self, "view", None):
            return False

        product = self.remote_product.local_instance
        assign_exists = SalesChannelViewAssign.objects.filter(
            product=product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
        ).exists()

        if not assign_exists and self.remote_product.is_variation and self.remote_product.remote_parent_product:
            assign_exists = SalesChannelViewAssign.objects.filter(
                product=self.remote_product.remote_parent_product.local_instance,
                sales_channel=self.sales_channel,
                sales_channel_view=self.view,
            ).exists()

        if not assign_exists:
            return False

        self.remote_instance, _ = self.remote_model_class.objects.get_or_create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
        return True

    def preflight_process(self) -> None:
        value = self.get_ean_code_value()
        self._ean_value = value if value not in (None, "") else None

    def build_payload(self) -> None:
        self.payload = {"ean_code": self._ean_value}

    def needs_update(self) -> bool:
        if self.get_value_only:
            return True

        current_value = self.remote_instance.ean_code or ""
        expected = self._ean_value or ""
        return expected != current_value

    def update_remote(self):
        return self.send_inventory_payload()

    def post_update_process(self) -> None:
        new_value = self._ean_value
        if self.remote_instance.ean_code != new_value:
            self.remote_instance.ean_code = new_value

    def run(self):
        if self.get_value_only:
            if not self.preflight_check():
                return None

            self.preflight_process()
            return self._ean_value

        return super().run()


EbayInventoryItemPayloadMixin.remote_eancode_update_factory = EbayEanCodeUpdateFactory
