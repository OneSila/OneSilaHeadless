from __future__ import annotations

import json
from typing import Any

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin


class MiraklProductsImportClient(GetMiraklAPIMixin):
    product_reference_batch_size = 100

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel

    def get_offers_page(self, *, offset: int = 0, max_items: int | None = None) -> dict[str, Any]:
        effective_page_size = min(100, max_items or self.default_page_size)
        payload = self.mirakl_get(
            path="/api/offers",
            params={
                "offset": max(offset, 0),
                "max": effective_page_size,
            },
        )
        self._log_response(
            path="/api/offers",
            params={
                "offset": max(offset, 0),
                "max": effective_page_size,
            },
            payload=payload,
        )
        offers = payload.get("offers") or []
        if not isinstance(offers, list):
            offers = []
        return {
            "offers": [offer for offer in offers if isinstance(offer, dict)],
            "total_count": payload.get("total_count"),
        }

    def get_products_offers_by_references(self, *, product_references: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return self._get_products_by_references(
            path="/api/products/offers",
            product_references=product_references,
            extra_params={"all_offers": True},
        )

    def get_products_by_references(self, *, product_references: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return self._get_products_by_references(
            path="/api/products",
            product_references=product_references,
        )

    def _get_products_by_references(
        self,
        *,
        path: str,
        product_references: list[tuple[str, str]],
        extra_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_references = self._normalize_product_references(product_references=product_references)
        if not normalized_references:
            return []

        collected_products: list[dict[str, Any]] = []
        for offset in range(0, len(normalized_references), self.product_reference_batch_size):
            chunk = normalized_references[offset:offset + self.product_reference_batch_size]
            params = {
                **(extra_params or {}),
                "product_references": self._format_product_references(product_references=chunk),
            }
            payload = self.mirakl_get(
                path=path,
                params=params,
            )
            self._log_response(
                path=path,
                params=params,
                payload=payload,
            )
            products = payload.get("products") or []
            if not isinstance(products, list):
                continue
            collected_products.extend(product for product in products if isinstance(product, dict))

        return collected_products

    def _log_response(self, *, path: str, params: dict[str, Any], payload: dict[str, Any]) -> None:
        label = {
            "/api/offers": "Mirakl import OF response",
            "/api/products/offers": "Mirakl import P11 response",
            "/api/products": "Mirakl import P31 response",
        }.get(path, "Mirakl import response")
        print(
            f"{label} "
            f"path={path} "
            f"params={json.dumps(params, sort_keys=True, default=str, ensure_ascii=False)} "
            f"payload={json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)}"
        )

    def _normalize_product_references(self, *, product_references: list[tuple[str, str]]) -> list[tuple[str, str]]:
        normalized_references: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for reference_type, reference in product_references:
            normalized_reference_type = str(reference_type or "").strip().upper()
            normalized_reference = str(reference or "").strip()
            if not normalized_reference_type or not normalized_reference:
                continue
            if normalized_reference_type in {"SHOP_SKU", "SKU"}:
                continue
            normalized_key = (normalized_reference_type, normalized_reference)
            if normalized_key in seen:
                continue
            seen.add(normalized_key)
            normalized_references.append(normalized_key)
        return normalized_references

    def _format_product_references(self, *, product_references: list[tuple[str, str]]) -> str:
        return ",".join(
            f"{reference_type}|{reference}"
            for reference_type, reference in product_references
        )
