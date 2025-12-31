"""Refresh Shein product details after approval."""

from __future__ import annotations

import logging
from typing import Any

from collections.abc import Mapping

from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.factories.imports.product_helpers import (
    SheinProductImportHelpers,
)
from sales_channels.integrations.shein.factories.imports.product_parsers import (
    SheinProductImportPayloadParser,
)
from sales_channels.integrations.shein.models import (
    SheinProduct,
    SheinSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.shein.models import SheinImageProductAssociation


logger = logging.getLogger(__name__)


class SheinProductDetailRefreshFactory(SheinSignatureMixin, SheinProductImportHelpers):
    """Fetch latest Shein product details and refresh remote metadata."""

    def __init__(self, *, sales_channel, remote_product) -> None:
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self._payload_parser = SheinProductImportPayloadParser(sales_channel=sales_channel)

    def _resolve_spu_name(self) -> str | None:
        spu_name = (getattr(self.remote_product, "spu_name", None) or "").strip()
        if spu_name:
            return spu_name
        legacy = (getattr(self.remote_product, "remote_id", None) or "").strip()
        return legacy or None

    def _resolve_parent_remote_product(self, *, spu_name: str) -> SheinProduct | None:
        parent = (
            SheinProduct.objects.filter(
                sales_channel=self.sales_channel,
                spu_name=spu_name,
                is_variation=False,
            )
            .order_by("id")
            .first()
        )
        return parent or self.remote_product

    def _update_view_assign_links(
        self,
        *,
        local_product: Any | None,
        view_payloads: dict[str, dict[str, Any]],
        remote_product: SheinProduct,
    ) -> None:
        if local_product is None or not view_payloads:
            return

        for site_code, payload in view_payloads.items():
            if not site_code:
                continue
            link = payload.get("link") if isinstance(payload, Mapping) else None
            if not link:
                continue

            view = (
                SheinSalesChannelView.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=site_code,
                )
                .select_related()
                .first()
            )
            if view is None:
                continue

            assign, _ = SalesChannelViewAssign.objects.get_or_create(
                product=local_product,
                sales_channel_view=view,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                defaults={
                    "remote_product": remote_product,
                    "link": link,
                },
            )

            update_fields: list[str] = []
            if assign.remote_product_id != remote_product.id:
                assign.remote_product = remote_product
                update_fields.append("remote_product")
            if assign.link != link:
                assign.link = link
                update_fields.append("link")
            if update_fields:
                assign.save(update_fields=update_fields)

    def _update_image_associations(
        self,
        *,
        remote_product: SheinProduct,
        remote_id_map: dict[str, str],
        image_group_code: str | None,
    ) -> None:
        if not remote_id_map and not image_group_code:
            return

        associations = (
            SheinImageProductAssociation.objects.filter(
                sales_channel=self.sales_channel,
                remote_product=remote_product,
            )
            .select_related("local_instance")
            .order_by("local_instance__sort_order", "local_instance__id", "id")
        )

        for index, association in enumerate(associations):
            updated_fields: list[str] = []
            remote_id = remote_id_map.get(str(index))
            if remote_id and association.remote_id != remote_id:
                association.remote_id = remote_id
                updated_fields.append("remote_id")
            if image_group_code and association.image_group_code != image_group_code:
                association.image_group_code = image_group_code
                updated_fields.append("image_group_code")
            if updated_fields:
                association.save(update_fields=updated_fields)

    def run(self) -> dict[str, Any] | None:
        spu_name = self._resolve_spu_name()
        if not spu_name:
            logger.info(
                "Shein product detail refresh skipped: missing spu_name (remote_product_id=%s)",
                getattr(self.remote_product, "pk", None),
            )
            return None

        try:
            payload = self.get_product(spu_name=spu_name)
        except Exception as exc:  # pragma: no cover - network defensive guard
            logger.exception(
                "Shein product detail refresh failed for spu_name=%s: %s",
                spu_name,
                exc,
            )
            return None

        if not isinstance(payload, dict):
            return None

        parent_remote = self._resolve_parent_remote_product(spu_name=spu_name)
        view_payloads = self._collect_view_payloads(spu_payload=payload)
        self._update_view_assign_links(
            local_product=getattr(parent_remote, "local_instance", None),
            view_payloads=view_payloads,
            remote_product=parent_remote,
        )

        skc_list = payload.get("skcInfoList") or payload.get("skc_info_list") or []
        if not isinstance(skc_list, list):
            skc_list = []

        raw_spu_images = payload.get("spuImageInfoList") or payload.get("spu_image_info_list") or []
        spu_images = [entry for entry in raw_spu_images if isinstance(entry, Mapping)] if isinstance(raw_spu_images, list) else []

        parent_image_payload = None
        if spu_images:
            parent_image_payload = {"skcImageInfoList": spu_images}
        else:
            best_skc_payload = None
            best_count = 0
            for skc_payload in skc_list:
                if not isinstance(skc_payload, Mapping):
                    continue
                raw_skc_images = skc_payload.get("skcImageInfoList") or skc_payload.get("skc_image_info_list") or []
                if not isinstance(raw_skc_images, list):
                    continue
                image_count = sum(1 for entry in raw_skc_images if isinstance(entry, Mapping))
                if image_count > best_count:
                    best_count = image_count
                    best_skc_payload = skc_payload
            if best_skc_payload is not None and best_count:
                parent_image_payload = best_skc_payload

        if parent_image_payload is not None:
            _, parent_remote_id_map, parent_group_code = self._payload_parser.parse_images(
                skc_payload=parent_image_payload
            )
            self._update_image_associations(
                remote_product=parent_remote,
                remote_id_map=parent_remote_id_map,
                image_group_code=parent_group_code,
            )

        for skc_payload in skc_list:
            if not isinstance(skc_payload, Mapping):
                continue
            _, remote_id_map, image_group_code = self._payload_parser.parse_images(
                skc_payload=skc_payload
            )
            if not remote_id_map and not image_group_code:
                continue

            sku_list = skc_payload.get("skuInfoList") or skc_payload.get("sku_info_list") or []
            if not isinstance(sku_list, list):
                continue

            for sku_payload in sku_list:
                if not isinstance(sku_payload, Mapping):
                    continue
                local_sku = self._resolve_local_sku(sku_payload=sku_payload, fallback_sku=None)
                if not local_sku:
                    continue
                variation_remote = (
                    SheinProduct.objects.filter(
                        sales_channel=self.sales_channel,
                        remote_sku=local_sku,
                    )
                    .order_by("id")
                    .first()
                )
                if variation_remote is None:
                    continue
                self._update_image_associations(
                    remote_product=variation_remote,
                    remote_id_map=remote_id_map,
                    image_group_code=image_group_code,
                )

        return payload
