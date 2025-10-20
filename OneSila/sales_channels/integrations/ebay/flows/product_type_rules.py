"""Flows for synchronising eBay product type rules."""

from __future__ import annotations

from typing import Optional

from sales_channels.integrations.ebay.factories.sales_channels import (
    EbayProductTypeRuleFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProductType,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayProductTypeRuleSyncFlow:
    """Ensure local rule metadata mirrors the mapped eBay category."""

    def __init__(self, *, product_type_id: int) -> None:
        self.product_type_id = product_type_id

    def work(self) -> None:
        product_type = self._get_product_type()
        if product_type is None:
            return

        remote_id = (product_type.remote_id or "").strip()
        if not remote_id or not product_type.local_instance_id:
            return

        view = product_type.marketplace
        if view is None:
            return

        real_view_getter = getattr(view, "get_real_instance", None)
        if callable(real_view_getter):
            resolved_view = real_view_getter()
            if resolved_view is not None:
                view = resolved_view

        sales_channel = product_type.sales_channel
        if sales_channel is None:
            return

        real_channel_getter = getattr(sales_channel, "get_real_instance", None)
        if callable(real_channel_getter):
            resolved_channel = real_channel_getter()
            if resolved_channel is not None:
                sales_channel = resolved_channel

        if not isinstance(sales_channel, EbaySalesChannel):
            return

        language = self._resolve_language(
            view=view,
            sales_channel=sales_channel,
        )

        factory = EbayProductTypeRuleFactory(
            sales_channel=sales_channel,
            view=view,
            category_id=remote_id,
            category_tree_id=getattr(view, "default_category_tree_id", None),
            language=language,
        )
        factory.run()

    def _get_product_type(self) -> Optional[EbayProductType]:
        return (
            EbayProductType.objects.select_related("sales_channel", "marketplace", "multi_tenant_company")
            .prefetch_related("marketplace__remote_languages")
            .filter(id=self.product_type_id)
            .first()
        )

    @staticmethod
    def _resolve_language(
        *,
        view: Optional[EbaySalesChannelView],
        sales_channel: EbaySalesChannel,
    ) -> Optional[str]:
        remote_languages = getattr(view, "remote_languages", None)
        if remote_languages is not None:
            remote_language = remote_languages.first()
            if remote_language and remote_language.local_instance:
                return remote_language.local_instance

        company = getattr(sales_channel, "multi_tenant_company", None)
        return getattr(company, "language", None)
