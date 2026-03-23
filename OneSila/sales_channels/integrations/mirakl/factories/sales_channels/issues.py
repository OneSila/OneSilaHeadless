from __future__ import annotations

from datetime import timezone as datetime_timezone
from typing import Any

from django.db import transaction
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklEanCode,
    MiraklProduct,
    MiraklProductIssue,
    MiraklSalesChannelView,
)


class MiraklProductIssuesFetchFactory(GetMiraklAPIMixin):
    """Fetch and persist Mirakl product issues in full or differential mode."""

    MODE_DIFFERENTIAL = "differential"
    MODE_FULL = "full"

    def __init__(self, *, sales_channel, mode: str) -> None:
        self.sales_channel = sales_channel
        self.mode = mode

    def run(self) -> dict[str, Any]:
        if self.mode not in {self.MODE_DIFFERENTIAL, self.MODE_FULL}:
            raise ValueError(f"Unsupported Mirakl issues fetch mode: {self.mode}")

        boundary = timezone.now()
        if self.mode == self.MODE_DIFFERENTIAL and self.sales_channel.last_differential_issues_fetch is None:
            return {"skipped": True, "reason": "missing_differential_baseline"}

        payload = self._fetch_payload(boundary=boundary)
        if payload is None:
            self._handle_empty_payload(boundary=boundary)
            return {"skipped": False, "products": 0, "issues": 0}

        processed_products = 0
        created_issues = 0
        for record in payload:
            remote_product = self._resolve_remote_product(record=record)
            if remote_product is None:
                continue
            created_issues += self._sync_remote_product_issues(
                remote_product=remote_product,
                record=record,
            )
            processed_products += 1

        self._persist_boundary(boundary=boundary)
        return {"skipped": False, "products": processed_products, "issues": created_issues}

    def _fetch_payload(self, *, boundary) -> list[dict[str, Any]] | None:
        params = {
            "updated_to": self._format_datetime(value=boundary),
        }
        if self.mode == self.MODE_DIFFERENTIAL:
            params["updated_since"] = self._format_datetime(
                value=self.sales_channel.last_differential_issues_fetch,
            )

        response = self._request(
            method="GET",
            path="/api/mcm/products/sources/status/export",
            params=params,
            expected_statuses={200, 204},
        )
        if response.status_code == 204:
            return None

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("Mirakl issues export payload is not valid JSON.") from exc

        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        raise ValueError("Mirakl issues export payload did not contain a JSON list.")

    def _handle_empty_payload(self, *, boundary) -> None:
        if self.mode == self.MODE_FULL:
            MiraklProductIssue.objects.filter(
                remote_product__sales_channel=self.sales_channel,
            ).delete()
        self._persist_boundary(boundary=boundary)

    def _persist_boundary(self, *, boundary) -> None:
        update_fields: list[str] = []
        if self.mode == self.MODE_FULL:
            self.sales_channel.last_full_issues_fetch = boundary
            self.sales_channel.last_differential_issues_fetch = boundary
            update_fields.extend(["last_full_issues_fetch", "last_differential_issues_fetch"])
        else:
            self.sales_channel.last_differential_issues_fetch = boundary
            update_fields.append("last_differential_issues_fetch")
        self.sales_channel.save(update_fields=update_fields)

    def _resolve_remote_product(self, *, record: dict[str, Any]) -> MiraklProduct | None:
        provider_identifier = str(record.get("provider_unique_identifier") or "").strip()
        if provider_identifier:
            match = self._match_remote_product_by_sku(identifier=provider_identifier)
            if match is not None:
                return match

        for identifier in record.get("unique_identifiers") or []:
            if not isinstance(identifier, dict):
                continue
            code = str(identifier.get("code") or "").strip().upper()
            value = str(identifier.get("value") or "").strip()
            if not value:
                continue
            if code in {"SHOP_SKU", "SKU"}:
                match = self._match_remote_product_by_sku(identifier=value)
            elif code == "EAN":
                match = self._match_remote_product_by_ean(identifier=value)
            else:
                match = None
            if match is not None:
                return match
        return None

    def _match_remote_product_by_sku(self, *, identifier: str) -> MiraklProduct | None:
        return (
            MiraklProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_sku=identifier,
            )
            .order_by("id")
            .first()
        )

    def _match_remote_product_by_ean(self, *, identifier: str) -> MiraklProduct | None:
        ean_match = (
            MiraklEanCode.objects.filter(
                remote_product__sales_channel=self.sales_channel,
                ean_code=identifier,
            )
            .select_related("remote_product")
            .order_by("id")
            .first()
        )
        if ean_match is None or ean_match.remote_product is None:
            return None

        remote_product = ean_match.remote_product
        get_real_instance = getattr(remote_product, "get_real_instance", None)
        if callable(get_real_instance):
            remote_product = get_real_instance()

        return remote_product if isinstance(remote_product, MiraklProduct) else None

    def _sync_remote_product_issues(self, *, remote_product: MiraklProduct, record: dict[str, Any]) -> int:
        issue_payloads = self._build_issue_payloads(record=record)
        with transaction.atomic():
            MiraklProductIssue.objects.filter(remote_product=remote_product).delete()
            created_issues = 0
            for issue_payload in issue_payloads:
                views = self._resolve_views(channel_codes=issue_payload.pop("channel_codes"))
                issue = MiraklProductIssue.objects.create(
                    multi_tenant_company=remote_product.multi_tenant_company,
                    remote_product=remote_product,
                    **issue_payload,
                )
                if views:
                    issue.views.set(views)
                created_issues += 1
        return created_issues

    def _build_issue_payloads(self, *, record: dict[str, Any]) -> list[dict[str, Any]]:
        issue_payloads: list[dict[str, Any]] = []
        for warning in record.get("warnings") or []:
            if not isinstance(warning, dict):
                continue
            issue_payloads.append(
                {
                    "main_code": str(warning.get("code") or "").strip() or None,
                    "code": str(warning.get("code") or "").strip() or None,
                    "message": str(warning.get("message") or "").strip() or None,
                    "severity": "WARNING",
                    "reason_label": None,
                    "attribute_code": str(warning.get("attribute_code") or "").strip() or None,
                    "is_rejected": False,
                    "raw_data": {
                        "source": "warning",
                        "record": record,
                        "warning": warning,
                    },
                    "channel_codes": [],
                }
            )

        for error in record.get("errors") or []:
            if not isinstance(error, dict):
                continue
            parent_code = str(error.get("code") or "").strip() or None
            parent_message = str(error.get("message") or "").strip() or None
            channel_codes = self._normalize_channel_codes(raw_channels=error.get("channels"))
            rejection_details = error.get("rejection_details")
            if isinstance(rejection_details, dict):
                issue_payloads.append(
                    {
                        "main_code": parent_code,
                        "code": str(rejection_details.get("reason_code") or "").strip() or None,
                        "message": self._compose_message(
                            parent_message=parent_message,
                            detail_message=str(rejection_details.get("message") or "").strip() or None,
                        ),
                        "severity": "ERROR",
                        "reason_label": str(rejection_details.get("reason_label") or "").strip() or None,
                        "attribute_code": None,
                        "is_rejected": True,
                        "raw_data": {
                            "source": "rejection_detail",
                            "record": record,
                            "error": error,
                            "rejection_details": rejection_details,
                        },
                        "channel_codes": channel_codes,
                    }
                )
                continue

            integration_details = error.get("integration_details") or []
            if isinstance(integration_details, list) and integration_details:
                for detail in integration_details:
                    if not isinstance(detail, dict):
                        continue
                    issue_payloads.append(
                        {
                            "main_code": parent_code,
                            "code": str(detail.get("code") or "").strip() or None,
                            "message": self._compose_message(
                                parent_message=parent_message,
                                detail_message=str(detail.get("message") or "").strip() or None,
                            ),
                            "severity": "ERROR",
                            "reason_label": None,
                            "attribute_code": str(detail.get("attribute_code") or "").strip() or None,
                            "is_rejected": False,
                            "raw_data": {
                                "source": "integration_detail",
                                "record": record,
                                "error": error,
                                "integration_detail": detail,
                            },
                            "channel_codes": channel_codes,
                        }
                    )
                continue

            issue_payloads.append(
                {
                    "main_code": parent_code,
                    "code": parent_code,
                    "message": parent_message,
                    "severity": "ERROR",
                    "reason_label": None,
                    "attribute_code": None,
                    "is_rejected": False,
                    "raw_data": {
                        "source": "error",
                        "record": record,
                        "error": error,
                    },
                    "channel_codes": channel_codes,
                }
            )

        return issue_payloads

    def _resolve_views(self, *, channel_codes: list[str]) -> list[MiraklSalesChannelView]:
        if not channel_codes:
            return []
        return list(
            MiraklSalesChannelView.objects.filter(
                sales_channel=self.sales_channel,
                remote_id__in=channel_codes,
            ).order_by("id")
        )

    def _normalize_channel_codes(self, *, raw_channels: Any) -> list[str]:
        if not isinstance(raw_channels, list):
            return []
        normalized: list[str] = []
        for item in raw_channels:
            if isinstance(item, dict):
                value = str(item.get("code") or "").strip()
            else:
                value = str(item or "").strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    def _compose_message(self, *, parent_message: str | None, detail_message: str | None) -> str | None:
        parts = [part for part in [parent_message, detail_message] if part]
        if not parts:
            return None
        return " | ".join(parts)

    def _format_datetime(self, *, value) -> str:
        if value is None:
            raise ValueError("Mirakl issues fetch date boundary is missing.")
        normalized = value.astimezone(datetime_timezone.utc).replace(microsecond=0)
        return normalized.isoformat().replace("+00:00", "Z")
