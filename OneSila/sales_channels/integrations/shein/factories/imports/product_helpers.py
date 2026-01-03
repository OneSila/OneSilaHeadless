"""Helper utilities for Shein product imports."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from sales_channels.integrations.shein.models import SheinProduct


class SheinProductImportHelpers:
    _EAN_DIGITS_RE = re.compile(r"\D+")

    def _load_spu_index(self) -> list[str]:
        if self._spu_index is not None:
            return self._spu_index

        spu_names: list[str] = []
        for record in self.get_all_products(skip_failed_page=True, page_size=400):
            if not isinstance(record, Mapping):
                continue
            spu_name = self._extract_spu_name(payload=record)
            if not spu_name:
                continue
            spu_names.append(spu_name)

        self._spu_index = spu_names
        return spu_names

    def _extract_spu_name(self, *, payload: Mapping[str, Any]) -> str | None:
        for key in ("spuName", "spu_name"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_skc_name(self, *, payload: Mapping[str, Any] | None) -> str | None:
        if not isinstance(payload, Mapping):
            return None
        value = payload.get("skcName") or payload.get("skc_name")
        return value.strip() if isinstance(value, str) and value.strip() else None

    def _extract_sku_code(self, *, payload: Mapping[str, Any] | None) -> str | None:
        if not isinstance(payload, Mapping):
            return None
        value = payload.get("skuCode") or payload.get("sku_code")
        return value.strip() if isinstance(value, str) and value.strip() else None

    def _extract_category_id(self, *, payload: Mapping[str, Any]) -> str | None:
        value = payload.get("categoryId") or payload.get("category_id")
        return str(value).strip() if value not in (None, "") else None

    def _extract_product_type_id(self, *, payload: Mapping[str, Any]) -> str | None:
        value = payload.get("productTypeId") or payload.get("product_type_id")
        return str(value).strip() if value not in (None, "") else None

    def _collect_sku_entries(self, *, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        skc_list = payload.get("skcInfoList") or payload.get("skc_info_list") or []
        if not isinstance(skc_list, list):
            return entries

        for skc in skc_list:
            if not isinstance(skc, Mapping):
                continue
            sku_list = skc.get("skuInfoList") or skc.get("sku_info_list") or []
            if not isinstance(sku_list, list):
                continue
            for sku in sku_list:
                if not isinstance(sku, Mapping):
                    continue
                entries.append({"skc": skc, "sku": sku})

        return entries

    def _resolve_local_sku(
        self,
        *,
        sku_payload: Mapping[str, Any] | None,
        fallback_sku: str | None,
    ) -> str | None:
        if isinstance(sku_payload, Mapping):
            for key in ("supplierSku", "supplier_sku", "supplierSkuCode", "supplier_sku_code"):
                value = sku_payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            for key in ("skuCode", "sku_code"):
                value = sku_payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return fallback_sku.strip() if isinstance(fallback_sku, str) and fallback_sku.strip() else None

    def _resolve_active_status(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        is_variation: bool,
    ) -> bool:
        def _active_from_shelf(*, records: list[dict[str, Any]]) -> bool | None:
            for entry in records:
                status = entry.get("shelfStatus") or entry.get("shelf_status")
                if status is None:
                    continue
                try:
                    return int(status) == 1
                except (TypeError, ValueError):
                    continue
            return None

        if isinstance(sku_payload, Mapping):
            mall_state = sku_payload.get("mallState") or sku_payload.get("mall_state")
            if mall_state is not None:
                try:
                    return int(mall_state) == 1
                except (TypeError, ValueError):
                    pass

        if isinstance(skc_payload, Mapping):
            shelf_records = skc_payload.get("shelfStatusInfoList") or skc_payload.get("shelf_status_info_list") or []
            if isinstance(shelf_records, list):
                resolved = _active_from_shelf(records=[r for r in shelf_records if isinstance(r, dict)])
                if resolved is not None:
                    return resolved

        if is_variation:
            return True

        skc_list = spu_payload.get("skcInfoList") or spu_payload.get("skc_info_list") or []
        if isinstance(skc_list, list):
            for skc in skc_list:
                if not isinstance(skc, Mapping):
                    continue
                shelf_records = skc.get("shelfStatusInfoList") or skc.get("shelf_status_info_list") or []
                if isinstance(shelf_records, list):
                    resolved = _active_from_shelf(records=[r for r in shelf_records if isinstance(r, dict)])
                    if resolved:
                        return True
                sku_list = skc.get("skuInfoList") or skc.get("sku_info_list") or []
                if isinstance(sku_list, list):
                    for sku in sku_list:
                        if not isinstance(sku, Mapping):
                            continue
                        mall_state = sku.get("mallState") or sku.get("mall_state")
                        if mall_state is None:
                            continue
                        try:
                            if int(mall_state) == 1:
                                return True
                        except (TypeError, ValueError):
                            continue

        return False

    def _extract_ean_code(self, *, sku_payload: Mapping[str, Any] | None) -> str | None:
        if not isinstance(sku_payload, Mapping):
            return None

        supplier_info = sku_payload.get("skuSupplierInfo") or sku_payload.get("sku_supplier_info") or {}
        if not isinstance(supplier_info, Mapping):
            supplier_info = {}
        barcode_list = supplier_info.get("supplierBarcodeList") or supplier_info.get("supplier_barcode_list") or []
        if not isinstance(barcode_list, list):
            barcode_list = []

        for entry in barcode_list:
            if not isinstance(entry, Mapping):
                continue
            barcode = entry.get("barcode") or entry.get("supplierBarcode")
            if isinstance(barcode, str) and barcode.strip():
                digits = self._EAN_DIGITS_RE.sub("", barcode)
                if digits:
                    return digits[:32]
        return None

    def _collect_view_payloads(self, *, spu_payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        view_payloads: dict[str, dict[str, Any]] = {}
        skc_list = spu_payload.get("skcInfoList") or spu_payload.get("skc_info_list") or []
        if not isinstance(skc_list, list):
            return view_payloads

        for skc in skc_list:
            if not isinstance(skc, Mapping):
                continue
            shelf_list = skc.get("shelfStatusInfoList") or skc.get("shelf_status_info_list") or []
            if isinstance(shelf_list, list):
                for entry in shelf_list:
                    if not isinstance(entry, Mapping):
                        continue
                    site = entry.get("siteAbbr") or entry.get("site_abbr")
                    if not site:
                        continue
                    view_payloads.setdefault(str(site).strip(), {})["link"] = entry.get("link")
            sku_list = skc.get("skuInfoList") or skc.get("sku_info_list") or []
            if isinstance(sku_list, list):
                for sku in sku_list:
                    if not isinstance(sku, Mapping):
                        continue
                    price_list = sku.get("priceInfoList") or sku.get("price_info_list") or []
                    if not isinstance(price_list, list):
                        continue
                    for price_entry in price_list:
                        if not isinstance(price_entry, Mapping):
                            continue
                        site = price_entry.get("site")
                        if not site:
                            continue
                        view_payloads.setdefault(str(site).strip(), {})

        return view_payloads

    def _get_remote_product(
        self,
        *,
        sku: str | None,
        spu_payload: Mapping[str, Any],
        sku_payload: Mapping[str, Any] | None,
        is_variation: bool,
    ) -> SheinProduct | None:
        base_qs = SheinProduct.objects.filter(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        ).select_related("local_instance")

        if sku:
            remote_product = base_qs.filter(remote_sku=sku).first()
            if remote_product:
                return remote_product

        if is_variation:
            sku_code = self._extract_sku_code(payload=sku_payload)
            if sku_code:
                return base_qs.filter(remote_id=sku_code).first()
            return None

        spu_name = self._extract_spu_name(payload=spu_payload)
        if spu_name:
            return base_qs.filter(remote_id=spu_name).first()

        return None
