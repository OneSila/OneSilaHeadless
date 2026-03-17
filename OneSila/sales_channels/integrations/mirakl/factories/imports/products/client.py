from __future__ import annotations

import pprint
import time
from typing import Any

import requests

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin


class MiraklProductsImportClient(GetMiraklAPIMixin):
    debug_sleep_seconds = 60
    OFFER_EXPORT_FIELDS = [
        "active",
        "allow_quote_requests",
        "available_end_date",
        "available_start_date",
        "channels",
        "currency_iso_code",
        "date_created",
        "deleted",
        "description",
        "eco_contributions",
        "favorite_rank",
        "fulfillment",
        "is_professional",
        "last_updated",
        "leadtime_to_ship",
        "logistic_class",
        "max_order_quantity",
        "measurement",
        "min_order_quantity",
        "min_shipping_price",
        "min_shipping_price_additional",
        "min_shipping_type",
        "min_shipping_zone",
        "model",
        "msrp",
        "offer_additional_fields",
        "offer_id",
        "package_quantity",
        "premium",
        "price_additional_info",
        "prices",
        "product_sku",
        "product_tax_code",
        "quantity",
        "retail_prices",
        "shipping_types",
        "shop_id",
        "shop_name",
        "shop_sku",
        "state_code",
        "warehouses",
    ]

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel

    def _debug_print_response(self, *, label: str, payload: Any) -> None:
        # @TODO: Remove this before deploy
        print(f"------------------------------------------------- RESPONSE FOR {label}")
        pprint.pprint(payload)
        if label.startswith("A01 "):
            return
        if label.startswith("OF52 REQUEST "):
            return
        if label.startswith("OF53 /"):
            return
        time.sleep(self.debug_sleep_seconds)

    def get_account_info(self) -> dict[str, Any]:
        response = self.mirakl_get(
            path="/api/account",
        )
        self._debug_print_response(label="A01 /api/account", payload=response)
        if not isinstance(response, dict):
            return {}
        return response

    def start_full_offer_export(self) -> dict[str, Any]:
        payload = {
            "export_type": "application/json",
            "include_inactive_offers": True,
            "items_per_chunk": 10000,
            "models": ["MARKETPLACE"],
            "include_fields": self.OFFER_EXPORT_FIELDS,
        }
        self._debug_print_response(
            label="OF52 REQUEST /api/offers/export/async",
            payload=payload,
        )
        response = self.mirakl_post(
            path="/api/offers/export/async",
            payload=payload,
            expected_statuses={200},
        )
        self._debug_print_response(label="OF52 /api/offers/export/async", payload=response)
        return response

    def get_offer_export_status(self, *, tracking_id: str) -> dict[str, Any]:
        response = self.mirakl_get(
            path=f"/api/offers/export/async/status/{tracking_id}",
        )
        self._debug_print_response(
            label=f"OF53 /api/offers/export/async/status/{tracking_id}",
            payload=response,
        )
        return response

    def download_json_chunk(self, *, url: str) -> list[dict[str, Any]]:
        response = requests.get(
            url,
            headers=self.get_mirakl_headers(),
            timeout=self.default_timeout,
            verify=self.sales_channel.verify_ssl,
        )
        if response.status_code != 200:
            raise ValueError(f"Mirakl chunk download failed with status {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("Mirakl chunk payload is not valid JSON.") from exc
        self._debug_print_response(label=f"OF53 CHUNK {url}", payload=payload)

        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("offers", "items", "data"):
                candidate = payload.get(key)
                if isinstance(candidate, list):
                    return [item for item in candidate if isinstance(item, dict)]
        raise ValueError("Mirakl chunk payload did not contain a JSON list.")

    def get_products_offers(self, *, product_ids: list[str]) -> list[dict[str, Any]]:
        if not product_ids:
            return []
        payload = self.mirakl_get(
            path="/api/products/offers",
            params={"product_ids": ",".join(product_ids)},
        )
        self._debug_print_response(
            label=f"P11 /api/products/offers product_ids={','.join(product_ids)}",
            payload=payload,
        )
        products = payload.get("products") or []
        if not isinstance(products, list):
            return []
        return [item for item in products if isinstance(item, dict)]

    def get_products_by_references(self, *, product_references: list[tuple[str, str]]) -> list[dict[str, Any]]:
        serialized_references = [
            f"{reference_type}|{reference}"
            for reference_type, reference in product_references
            if str(reference_type or "").strip() and str(reference or "").strip()
        ]
        if not serialized_references:
            return []

        payload = self.mirakl_get(
            path="/api/products",
            params={"product_references": ",".join(serialized_references)},
        )
        self._debug_print_response(
            label=f"P31 /api/products product_references={','.join(serialized_references)}",
            payload=payload,
        )
        products = payload.get("products") or []
        if not isinstance(products, list):
            return []
        return [item for item in products if isinstance(item, dict)]
