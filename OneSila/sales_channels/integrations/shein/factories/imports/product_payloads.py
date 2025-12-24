"""Payload shaping helpers for Shein product imports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from products.product_types import CONFIGURABLE, SIMPLE
from sales_channels.integrations.shein.models import SheinSalesChannelView


class SheinProductImportPayloadMixin:
    def get__product_data(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        local_sku: str,
        is_variation: bool,
        is_configurable: bool,
        product_instance: Any | None = None,
        parent_sku: str | None = None,
    ) -> tuple[dict[str, Any], str | None, SheinSalesChannelView | None]:
        structured: dict[str, Any] = {
            "sku": local_sku,
            "type": CONFIGURABLE if is_configurable else SIMPLE,
            "active": self._resolve_active_status(
                spu_payload=spu_payload,
                skc_payload=skc_payload,
                sku_payload=sku_payload,
                is_variation=is_variation,
            ),
        }

        translations, language_code = self._payload_parser.parse_translations(
            spu_payload=spu_payload,
            skc_payload=skc_payload if is_variation else None,
        )
        if translations and self.sales_channel.sync_contents:
            structured["translations"] = translations
            structured["name"] = translations[0]["name"]
        else:
            structured["name"] = local_sku

        if self.sales_channel.sync_contents:
            images, image_map = self._payload_parser.parse_images(skc_payload=skc_payload)
            if images:
                structured["images"] = images
                if image_map:
                    structured["__image_index_to_remote_id"] = image_map

        if not is_configurable and self.sales_channel.sync_prices:
            prices, sales_pricelist_items = self._payload_parser.parse_prices(
                sku_payload=sku_payload,
                local_product=product_instance,
            )
            if prices:
                structured["prices"] = prices
            if sales_pricelist_items:
                structured["sales_pricelist_items"] = sales_pricelist_items

        include_sku_fields = bool(sku_payload and (is_variation or not is_configurable))
        attributes, mirror_map = self._payload_parser.parse_attributes(
            spu_payload=spu_payload,
            skc_payload=skc_payload,
            sku_payload=sku_payload,
            product_type_id=self._extract_product_type_id(payload=spu_payload),
            is_variation=is_variation,
            include_sku_fields=include_sku_fields,
            language_code=language_code,
        )
        if attributes:
            structured["properties"] = attributes
        if mirror_map:
            structured["__mirror_product_properties_map"] = mirror_map

        ean_code = self._extract_ean_code(sku_payload=sku_payload)
        if ean_code and self.sales_channel.sync_ean_codes and not is_configurable:
            structured["ean_code"] = ean_code

        if parent_sku and is_variation:
            structured["configurable_parent_skus"] = [parent_sku]

        return structured, language_code, None
