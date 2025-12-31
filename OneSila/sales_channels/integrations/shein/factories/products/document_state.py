import json
import logging
from typing import Any, Optional

from django.db.utils import OperationalError, ProgrammingError
from integrations.models import IntegrationLog
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import SheinProductIssue
from sales_channels.integrations.shein.helpers.document_state import (
    shein_aggregate_document_states_to_status,
)
from sales_channels.integrations.shein.factories.imports.product_refresh import (
    SheinProductDetailRefreshFactory,
)
from sales_channels.models.products import RemoteProduct


logger = logging.getLogger(__name__)


class SheinProductDocumentStateFactory(SheinSignatureMixin):
    """Query Shein audit status for a published product and log failures."""

    query_document_state_path = "/open-api/goods/query-document-state"

    def __init__(self, *, sales_channel, remote_product) -> None:
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self.spu_name: str = ""
        self.version: Optional[str] = None
        self.response_data: dict[str, Any] = {}
        self.failures: list[dict[str, Any]] = []

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

    def validate(self) -> None:
        spu_name = (getattr(self.remote_product, "spu_name", None) or "").strip()
        if not spu_name:
            legacy = (getattr(self.remote_product, "remote_id", None) or "").strip()
            if legacy:
                spu_name = legacy
                try:
                    setattr(self.remote_product, "spu_name", spu_name)
                    self.remote_product.save(update_fields=["spu_name"])
                except Exception:
                    pass


        if not spu_name:
            self.remote_product.add_user_error(
                action=IntegrationLog.ACTION_UPDATE,
                response="Missing spu_name for Shein remote product; publish/create the product first.",
                payload={"remote_product_id": getattr(self.remote_product, "id", None)},
                error_traceback="",
                identifier="SheinProductDocumentState:missing_spu_name",
                remote_product=self.remote_product,
            )
            raise ValidationError(_("Shein product is missing spu_name; publish the product first."))

        self.spu_name = spu_name

    def build_payload(self) -> dict[str, Any]:
        entry: dict[str, Any] = {"spuName": self.spu_name}
        self.version = self._resolve_latest_version()
        if self.version:
            entry["version"] = self.version
        return {"spuList": [entry]}

    def _extract_failed_reason_messages(self, *, failures: list[dict[str, Any]]) -> list[str]:
        messages: list[str] = []
        for failure in failures:
            failed_reason = failure.get("failedReason") or []
            if isinstance(failed_reason, list):
                for reason in failed_reason:
                    text = str(reason).strip()
                    if text:
                        messages.append(text)
            else:
                text = str(failed_reason).strip()
                if text:
                    messages.append(text)

        return list(dict.fromkeys(messages))

    def _handle_review_failures(self, *, failures: list[dict[str, Any]]) -> None:
        if not failures:
            return

        if not self.remote_product:
            return

        messages = self._extract_failed_reason_messages(failures=failures)
        if not messages:
            return

        error_message = "Shein product review failed: {}".format("; ".join(messages))
        self.remote_product.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response="",
            payload={
                "spu_name": self.spu_name,
                "failure_count": len(messages),
                "failed_reason": messages,
            },
            identifier="SheinProductDocumentState:review_failed",
            remote_product=self.remote_product,
            error_message=error_message,
        )
        self.remote_product.refresh_status(
            override_status=self.remote_product.STATUS_APPROVAL_REJECTED,
        )

    def fetch(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.shein_post(path=self.query_document_state_path, payload=payload)
        response_data = response.json() if hasattr(response, "json") else {}
        return response_data if isinstance(response_data, dict) else {"response": response_data}

    def persist_issues(self) -> None:
        try:
            for failure in self.failures:
                SheinProductIssue.upsert_from_document_state(
                    remote_product=self.remote_product,
                    record=failure,
                )
        except (OperationalError, ProgrammingError):
            logger.info("SheinProductIssue table not available yet; skipping issue upserts.")

    def update_remote_product_status(self) -> None:
        document_states: list[int | None] = []
        for failure in self.failures:
            value = failure.get("documentState")
            try:
                document_states.append(int(value) if value is not None else None)
            except (TypeError, ValueError):
                document_states.append(None)

        override = shein_aggregate_document_states_to_status(document_states=document_states)
        if not override:
            return

        previous_status = self.remote_product.status
        self.remote_product.refresh_status(override_status=override)

        if (
            previous_status == RemoteProduct.STATUS_PENDING_APPROVAL
            and override == RemoteProduct.STATUS_COMPLETED
        ):
            SheinProductDetailRefreshFactory(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            ).run()

    def log(self) -> None:
        fetched_at = now().strftime("%Y-%m-%d %H:%M:%S")
        self.remote_product.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response=json.dumps(self.response_data, ensure_ascii=False),
            payload={"spu_name": self.spu_name, "version": self.version, "failure_count": len(self.failures)},
            identifier="SheinProductDocumentState",
            remote_product=self.remote_product,
            error_message=f"Fetched issues at {fetched_at}",
        )

    def run(self) -> dict[str, Any]:
        self.validate()
        payload = self.build_payload()
        self.response_data = self.fetch(payload=payload)
        self.failures = self._extract_failures(response_data=self.response_data)
        self.persist_issues()
        self.update_remote_product_status()
        self._handle_review_failures(failures=self.failures)
        self.log()
        return self.response_data

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
                failed_reason = skc.get("failedReason") or []
                if not isinstance(failed_reason, list):
                    failed_reason = []

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
