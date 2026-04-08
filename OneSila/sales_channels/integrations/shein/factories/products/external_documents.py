from __future__ import annotations

from typing import Any

from integrations.models import IntegrationLog
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.helpers.certificate_types import (
    PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER,
    RESOLVED_EXTERNAL_DOCUMENTS_IDENTIFIER,
    is_certificate_type_uploadable,
)
from sales_channels.integrations.shein.models import SheinDocumentType
from sales_channels.models.products import RemoteProduct


class SheinProductExternalDocumentsFactory(SheinSignatureMixin):
    def __init__(self, *, sales_channel, remote_product) -> None:
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self.spu_name = self._resolve_spu_name()

    def _resolve_spu_name(self) -> str:
        return str(
            getattr(self.remote_product, "spu_name", None)
            or getattr(self.remote_product, "remote_id", None)
            or ""
        ).strip()

    @staticmethod
    def _is_dimension_one_certificate_rule(*, record: dict[str, Any]) -> bool:
        dimension = str(record.get("certificateDimension") or "").strip()
        return not dimension or dimension == "1"

    @staticmethod
    def _is_required_certificate_rule(*, record: dict[str, Any]) -> bool:
        value = record.get("isRequired")
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return False

    def _get_certificate_rule_records(self) -> list[dict[str, Any]]:
        if not self.spu_name:
            return []

        records = self.get_certificate_rule_by_product_spu(spu_name=self.spu_name)
        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    def _get_document_type_name_by_remote_id(self, *, remote_ids: list[str]) -> dict[str, str]:
        if not remote_ids:
            return {}

        document_types = (
            SheinDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id__in=remote_ids,
            )
            .only("remote_id", "translated_name", "name")
        )
        names_by_remote_id: dict[str, str] = {}
        for document_type in document_types:
            remote_id = str(document_type.remote_id or "").strip()
            if not remote_id:
                continue
            label = (
                str(document_type.translated_name or "").strip()
                or str(document_type.name or "").strip()
                or remote_id
            )
            names_by_remote_id[remote_id] = label
        return names_by_remote_id

    def get_missing_external_document_records(self) -> list[dict[str, str]]:
        certificate_rule_records = self._get_certificate_rule_records()
        missing_remote_ids: list[str] = []
        rule_name_by_remote_id: dict[str, str] = {}

        for record in certificate_rule_records:
            if not self._is_dimension_one_certificate_rule(record=record):
                continue
            if not self._is_required_certificate_rule(record=record):
                continue

            certificate_type_id = str(record.get("certificateTypeId") or "").strip()
            if not certificate_type_id:
                continue
            if is_certificate_type_uploadable(
                sales_channel=self.sales_channel,
                certificate_type_id=certificate_type_id,
            ):
                continue
            if not bool(record.get("certificateMissStatus")):
                continue

            missing_remote_ids.append(certificate_type_id)
            if certificate_type_id not in rule_name_by_remote_id:
                rule_name_by_remote_id[certificate_type_id] = str(
                    record.get("certificateTypeValue")
                    or record.get("certificateType")
                    or ""
                ).strip()

        if not missing_remote_ids:
            return []

        names_by_remote_id = self._get_document_type_name_by_remote_id(
            remote_ids=missing_remote_ids,
        )
        missing_records: list[dict[str, str]] = []
        seen_remote_ids: set[str] = set()
        for remote_id in missing_remote_ids:
            if remote_id in seen_remote_ids:
                continue
            seen_remote_ids.add(remote_id)
            label = (
                names_by_remote_id.get(remote_id)
                or rule_name_by_remote_id.get(remote_id)
                or remote_id
            )
            missing_records.append(
                {
                    "remote_id": remote_id,
                    "label": label,
                }
            )

        return missing_records

    def _build_pending_message(self, *, missing_records: list[dict[str, str]]) -> str:
        labels = ", ".join(record["label"] for record in missing_records)
        return (
            "Please go in the SHEIN compliance manager and add the following documents for "
            f"SPU {self.spu_name}: {labels}."
        )

    def apply(self, *, log_missing: bool, action: str = IntegrationLog.ACTION_UPDATE) -> bool:
        missing_records = self.get_missing_external_document_records()
        if missing_records:
            update_fields: list[str] = []
            if self.remote_product.pending_external_documents is False:
                self.remote_product.pending_external_documents = True
                update_fields.append("pending_external_documents")
            if update_fields:
                self.remote_product.save(
                    update_fields=update_fields,
                    skip_status_check=True,
                )
            if log_missing:
                self.remote_product.add_log(
                    action=action,
                    response="",
                    payload={
                        "spu_name": self.spu_name,
                        "missing_document_remote_ids": [record["remote_id"] for record in missing_records],
                        "missing_document_labels": [record["label"] for record in missing_records],
                    },
                    identifier=PENDING_EXTERNAL_DOCUMENTS_IDENTIFIER,
                    remote_product=self.remote_product,
                    error_message=self._build_pending_message(missing_records=missing_records),
                )
            self.remote_product.refresh_status(
                override_status=RemoteProduct.STATUS_PENDING_EXTERNAL_DOCUMENTS,
            )
            return True

        if self.remote_product.pending_external_documents:
            self.remote_product.pending_external_documents = False
            self.remote_product.save(
                update_fields=["pending_external_documents"],
                skip_status_check=True,
            )
            self.remote_product.add_log(
                action=action,
                response="",
                payload={"spu_name": self.spu_name},
                identifier=RESOLVED_EXTERNAL_DOCUMENTS_IDENTIFIER,
                remote_product=self.remote_product,
                error_message=(
                    "All required external SHEIN compliance documents are now present. "
                    "The product has resumed the approval flow."
                ),
            )
            self.remote_product.refresh_status(
                override_status=RemoteProduct.STATUS_PENDING_APPROVAL,
            )

        return False
