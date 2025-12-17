from __future__ import annotations

import json
import logging
from typing import Any, Optional

from django.db.utils import OperationalError, ProgrammingError
from integrations.models import IntegrationLog
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import SheinProductIssue


logger = logging.getLogger(__name__)


class SheinProductDocumentStateFactory(SheinSignatureMixin):
    """Query Shein audit status for a published product and log failures."""

    query_document_state_path = "/open-api/goods/query-document-state"

    def __init__(self, *, sales_channel, remote_product) -> None:
        self.sales_channel = sales_channel
        self.remote_product = remote_product

    def _resolve_latest_version(self) -> Optional[str]:
        if not getattr(self.remote_product, "pk", None):
            return None

        log = (
            IntegrationLog.objects.filter(
                integration=self.sales_channel,
                object_id=self.remote_product.pk,
                identifier="SheinProductSubmission",
                status=IntegrationLog.STATUS_SUCCESS,
            )
            .order_by("-created_at")
            .first()
        )
        if not log or not isinstance(log.payload, dict):
            return None

        version = log.payload.get("version")
        return str(version) if version else None

    def run(self) -> dict[str, Any]:
        spu_name = getattr(self.remote_product, "remote_id", None)
        if not spu_name:
            raise ValueError("Shein remote product is missing spu_name (remote_id).")

        entry: dict[str, Any] = {"spuName": str(spu_name)}
        version = self._resolve_latest_version()
        if version:
            entry["version"] = version

        payload = {"spuList": [entry]}

        response = self.shein_post(path=self.query_document_state_path, payload=payload)
        response_data = response.json() if hasattr(response, "json") else {}

        failures = self._extract_failures(response_data=response_data)
        try:
            for failure in failures:
                SheinProductIssue.upsert_from_document_state(
                    remote_product=self.remote_product,
                    record=failure,
                )
        except (OperationalError, ProgrammingError):
            logger.info("SheinProductIssue table not available yet; skipping issue upserts.")

        self.remote_product.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response=json.dumps(response_data, ensure_ascii=False),
            payload={"spu_name": spu_name, "version": version, "failure_count": len(failures)},
            identifier="SheinProductDocumentState",
            remote_product=self.remote_product,
        )

        return response_data if isinstance(response_data, dict) else {"response": response_data}

    @staticmethod
    def _extract_failures(*, response_data: Any) -> list[dict[str, Any]]:
        if not isinstance(response_data, dict):
            return []

        info = response_data.get("info")
        if not isinstance(info, dict):
            return []

        records = info.get("data")
        if not isinstance(records, list):
            return []

        failures: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue

            spu_name = record.get("spuName")
            version = record.get("version")
            skc_list = record.get("skcList")
            if not isinstance(skc_list, list):
                continue

            for skc in skc_list:
                if not isinstance(skc, dict):
                    continue

                document_state = skc.get("documentState")
                failed_reason = skc.get("failedReason")
                if not failed_reason:
                    continue

                failures.append(
                    {
                        "spuName": spu_name,
                        "version": version,
                        "skcName": skc.get("skcName"),
                        "documentSn": skc.get("documentSn"),
                        "documentState": document_state,
                        "failedReason": failed_reason,
                    }
                )

        return failures
