import json
import logging
from typing import Any, Optional

from django.db.utils import OperationalError, ProgrammingError
from integrations.models import IntegrationLog
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinDocumentThroughProduct,
    SheinProduct,
    SheinProductIssue,
)
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
        logger.debug("Shein document state response: %s", response_data)
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

    def _get_status_target_remote_product_ids(self) -> list[int]:
        remote_product = self.remote_product
        if not getattr(remote_product, "pk", None):
            return []

        if getattr(remote_product, "is_variation", False) and getattr(remote_product, "remote_parent_product_id", None):
            return list(
                SheinProduct.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_parent_product_id=remote_product.remote_parent_product_id,
                    is_variation=True,
                ).values_list("id", flat=True)
            )

        if getattr(remote_product, "is_variation", False):
            return [remote_product.pk]

        variation_ids = list(
            SheinProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=remote_product,
                is_variation=True,
            ).values_list("id", flat=True)
        )
        if variation_ids:
            return variation_ids
        return [remote_product.pk]

    @staticmethod
    def _extract_certificate_sources(*, record: dict[str, Any]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []

        certificate_pool_list = record.get("certificatePoolList")
        if isinstance(certificate_pool_list, list):
            sources.extend(item for item in certificate_pool_list if isinstance(item, dict))

        other_source_list = record.get("otherSourceCertInfoList")
        if isinstance(other_source_list, list):
            sources.extend(item for item in other_source_list if isinstance(item, dict))

        return sources

    @staticmethod
    def _extract_source_certificate_urls(*, source: dict[str, Any]) -> set[str]:
        urls: set[str] = set()
        file_list = source.get("certificatePoolFileList")
        if not isinstance(file_list, list):
            return urls

        for file_payload in file_list:
            if not isinstance(file_payload, dict):
                continue
            certificate_url = str(file_payload.get("certificateUrl") or "").strip()
            if certificate_url:
                urls.add(certificate_url)
        return urls

    def sync_document_association_statuses(self) -> None:
        target_remote_product_ids = self._get_status_target_remote_product_ids()
        if not target_remote_product_ids:
            return

        try:
            certificate_records = self.get_certificate_rule_by_product_spu(spu_name=self.spu_name)
        except Exception:
            logger.exception(
                "Failed to fetch Shein certificate rules while syncing document statuses for channel=%s spu=%s",
                getattr(self.sales_channel, "id", None),
                self.spu_name,
            )
            return

        accepted_type_ids: set[str] = set()
        accepted_by_url: set[tuple[str, str]] = set()
        accepted_types_with_urls: set[str] = set()
        rejected_by_pqms: set[tuple[str, str]] = set()
        rejected_by_pool: set[tuple[str, str]] = set()
        rejected_by_url: set[tuple[str, str]] = set()

        for record in certificate_records:
            if not isinstance(record, dict):
                continue

            certificate_type_id = str(record.get("certificateTypeId") or "").strip()
            if not certificate_type_id:
                continue

            dimension = str(record.get("certificateDimension") or "").strip()
            if dimension and dimension != "1":
                continue

            certificate_missing = bool(record.get("certificateMissStatus"))
            for source in self._extract_certificate_sources(record=record):
                source_urls = self._extract_source_certificate_urls(source=source)
                if source_urls:
                    accepted_types_with_urls.add(certificate_type_id)

                if not certificate_missing:
                    for source_url in source_urls:
                        accepted_by_url.add((certificate_type_id, source_url))

                audit_status = str(source.get("auditStatus") or "").strip()
                if audit_status != "3":
                    continue

                pqms_certificate_sn = str(source.get("pqmsCertificateSn") or "").strip()
                certificate_pool_id = str(source.get("certificatePoolId") or "").strip()
                if pqms_certificate_sn:
                    rejected_by_pqms.add((certificate_type_id, pqms_certificate_sn))
                if certificate_pool_id:
                    rejected_by_pool.add((certificate_type_id, certificate_pool_id))
                for source_url in source_urls:
                    rejected_by_url.add((certificate_type_id, source_url))

            if not certificate_missing:
                accepted_type_ids.add(certificate_type_id)

        associations = (
            SheinDocumentThroughProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_product_id__in=target_remote_product_ids,
            )
            .filter(Q(remote_document__isnull=False))
            .select_related("remote_document", "remote_document__remote_document_type")
        )

        for association in associations.iterator():
            remote_document = getattr(association, "remote_document", None)
            remote_document_type = getattr(remote_document, "remote_document_type", None)
            certificate_type_id = str(getattr(remote_document_type, "remote_id", "") or "").strip()
            if not certificate_type_id:
                continue

            association_remote_id = str(getattr(association, "remote_id", "") or "").strip()
            certificate_pool_id = str(getattr(remote_document, "remote_id", "") or "").strip()
            remote_url = str(
                getattr(association, "remote_url", None)
                or getattr(remote_document, "remote_url", None)
                or ""
            ).strip()

            target_status: str | None = None
            if (certificate_type_id, association_remote_id) in rejected_by_pqms:
                target_status = SheinDocumentThroughProduct.STATUS_REJECTED
            elif (certificate_type_id, certificate_pool_id) in rejected_by_pool:
                target_status = SheinDocumentThroughProduct.STATUS_REJECTED
            elif remote_url and (certificate_type_id, remote_url) in rejected_by_url:
                target_status = SheinDocumentThroughProduct.STATUS_REJECTED
            elif remote_url and (certificate_type_id, remote_url) in accepted_by_url:
                target_status = SheinDocumentThroughProduct.STATUS_ACCEPTED
            elif (
                certificate_type_id in accepted_type_ids
                and certificate_type_id not in accepted_types_with_urls
            ):
                # Fallback for payloads where Shein does not return file URLs.
                target_status = SheinDocumentThroughProduct.STATUS_ACCEPTED

            if target_status and association.missing_status != target_status:
                association.missing_status = target_status
                association.save(update_fields=["missing_status"])

            if target_status == SheinDocumentThroughProduct.STATUS_REJECTED:
                self._upsert_rejected_document_issue(association=association)

    def _build_document_rejection_label(self, *, association: SheinDocumentThroughProduct) -> str:
        media_through = getattr(association, "local_instance", None)
        media = getattr(media_through, "media", None)
        local_document_type = getattr(media, "document_type", None)
        local_document_type_name = str(getattr(local_document_type, "name", "") or "").strip()
        if local_document_type_name:
            return local_document_type_name

        remote_document = getattr(association, "remote_document", None)
        remote_document_type = getattr(remote_document, "remote_document_type", None)
        remote_document_type_name = str(getattr(remote_document_type, "name", "") or "").strip()
        if remote_document_type_name:
            return remote_document_type_name

        return "Document"

    def _upsert_rejected_document_issue(self, *, association: SheinDocumentThroughProduct) -> None:
        rejection_label = self._build_document_rejection_label(association=association)
        reason = (
            f"Document '{rejection_label}' was rejected by Shein. "
            "Upload a valid replacement and retry sync."
        )
        record = {
            "spuName": self.spu_name,
            "version": self.version or "",
            "skcName": str(getattr(getattr(association, "remote_product", None), "skc_name", "") or "").strip(),
            "documentSn": str(getattr(association, "remote_id", "") or "").strip(),
            "documentState": 3,
            "failedReason": [reason],
        }
        if not record["documentSn"]:
            record["documentSn"] = str(getattr(getattr(association, "remote_document", None), "remote_id", "") or "").strip()
        if not record["documentSn"]:
            record["documentSn"] = f"REJECTED:{association.id}"

        try:
            SheinProductIssue.upsert_from_document_state(
                remote_product=self.remote_product,
                record=record,
            )
        except Exception:
            logger.exception(
                "Failed to upsert Shein rejected document issue for remote_product=%s association=%s",
                getattr(self.remote_product, "id", None),
                getattr(association, "id", None),
            )

    def update_remote_product_status(self) -> None:
        document_states: list[int | None] = []
        for failure in self.failures:
            value = failure.get("documentState")
            try:
                document_states.append(int(value) if value is not None else None)
            except (TypeError, ValueError):
                document_states.append(None)

        override = shein_aggregate_document_states_to_status(document_states=document_states)
        has_rejected_document_associations = bool(
            getattr(self.remote_product, "_has_rejected_document_associations", lambda: False)()
        )
        has_pending_document_associations = bool(
            getattr(self.remote_product, "_has_pending_document_associations", lambda: False)()
        )
        if has_rejected_document_associations:
            override = RemoteProduct.STATUS_APPROVAL_REJECTED
        elif (
            override == RemoteProduct.STATUS_COMPLETED
            and has_pending_document_associations
        ):
            override = RemoteProduct.STATUS_PENDING_APPROVAL
        elif not override and has_pending_document_associations:
            override = RemoteProduct.STATUS_PENDING_APPROVAL
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
        self.sync_document_association_statuses()
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
