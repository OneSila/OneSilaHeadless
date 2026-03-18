from __future__ import annotations

from typing import Any

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin


class MiraklProductsImportClient(GetMiraklAPIMixin):
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
        offers = payload.get("offers") or []
        if not isinstance(offers, list):
            offers = []
        return {
            "offers": [offer for offer in offers if isinstance(offer, dict)],
            "total_count": payload.get("total_count"),
        }

    def get_product_by_reference(self, *, reference_type: str, reference: str) -> dict[str, Any] | None:
        normalized_reference_type = str(reference_type or "").strip()
        normalized_reference = str(reference or "").strip()
        if not normalized_reference_type or not normalized_reference:
            return None

        response = self._request(
            method="GET",
            path="/api/products",
            params={
                "product_references": f"{normalized_reference_type}|{normalized_reference}",
            },
            expected_statuses={200, 404},
        )
        if response.status_code == 404:
            return None

        payload = self._json(response=response)
        products = payload.get("products") or []
        if not isinstance(products, list):
            return None
        for product in products:
            if isinstance(product, dict):
                return product
        return None
