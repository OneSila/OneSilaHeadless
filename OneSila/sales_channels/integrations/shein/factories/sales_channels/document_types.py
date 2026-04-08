"""Synchronize Shein certificate rules into remote document types."""

from __future__ import annotations

import logging
from typing import Any, Optional

from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import SheinDocumentType, SheinSalesChannel

logger = logging.getLogger(__name__)


class SheinCertificateRuleSyncFactory(SheinSignatureMixin):
    """Pull certificate rules per category and mirror them as ``SheinDocumentType`` rows."""

    store_level_certificate_dimension = 2

    def __init__(
        self,
        *,
        sales_channel: SheinSalesChannel,
        category_remote_id: Optional[str] = None,
        uploadable_certificate_type_ids: Optional[set[str]] = None,
    ) -> None:
        self.sales_channel = sales_channel
        self.category_remote_id = str(category_remote_id or "").strip()
        self.uploadable_certificate_type_ids = (
            {
                str(certificate_type_id).strip()
                for certificate_type_id in (uploadable_certificate_type_ids or set())
                if str(certificate_type_id).strip()
            }
            if uploadable_certificate_type_ids is not None
            else None
        )
        self.created_count = 0
        self.updated_count = 0
        self.rules_processed = 0
        self.categories_processed = 0

    def run(self, *, category_remote_id: Optional[str] = None) -> dict[str, int]:
        resolved_category_remote_id = str(
            category_remote_id if category_remote_id is not None else self.category_remote_id
        ).strip()
        if not resolved_category_remote_id:
            return {
                "categories_processed": 0,
                "rules_processed": 0,
                "document_types_created": 0,
                "document_types_updated": 0,
            }

        try:
            records = self.get_certificate_rule_by_category_id(
                category_id=resolved_category_remote_id,
            )
        except Exception:
            logger.exception(
                "Failed to fetch Shein certificate rules for channel=%s category=%s",
                getattr(self.sales_channel, "id", None),
                resolved_category_remote_id,
            )
            records = []
        self.categories_processed += 1
        for record in records:
            self._sync_certificate_rule_record(
                category_remote_id=resolved_category_remote_id,
                record=record,
            )

        return {
            "categories_processed": self.categories_processed,
            "rules_processed": self.rules_processed,
            "document_types_created": self.created_count,
            "document_types_updated": self.updated_count,
        }

    def _sync_certificate_rule_record(
        self,
        *,
        category_remote_id: str,
        record: dict[str, Any],
    ) -> None:
        certificate_dimension = self._safe_int(value=record.get("certificateDimension"))
        if certificate_dimension == self.store_level_certificate_dimension:
            return

        remote_id = self._safe_string(value=record.get("certificateTypeId"))
        if not remote_id:
            return

        name = self._safe_string(value=record.get("certificateTypeValue")) or remote_id
        is_required = self._coerce_bool(value=record.get("isRequired"))

        document_type, created = SheinDocumentType.objects.get_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            defaults={"name": name},
        )
        self.rules_processed += 1

        changed = False
        if not created and name and document_type.name != name:
            document_type.name = name
            changed = True

        if self.uploadable_certificate_type_ids is not None:
            uploadable = remote_id in self.uploadable_certificate_type_ids
            if document_type.uploadable != uploadable:
                document_type.uploadable = uploadable
                changed = True

        if is_required:
            changed = document_type.add_required_category(
                category_remote_id=category_remote_id,
                save=False,
            ) or changed
        else:
            changed = document_type.add_optional_category(
                category_remote_id=category_remote_id,
                save=False,
            ) or changed

        if created:
            self.created_count += 1

        if changed:
            document_type.save()
            if not created:
                self.updated_count += 1

    @staticmethod
    def _safe_int(*, value) -> Optional[int]:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def _safe_string(*, value) -> str:
        return str(value or "").strip()

    @staticmethod
    def _coerce_bool(*, value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return int(value) == 1

        normalized = str(value or "").strip().lower()
        return normalized in {"1", "true", "yes", "y"}
