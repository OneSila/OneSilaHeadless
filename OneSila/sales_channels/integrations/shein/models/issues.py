from __future__ import annotations

from typing import Any, Optional

from core import models


class SheinProductIssue(models.Model):
    """Store review/audit issues reported by Shein for submitted products."""

    remote_product = models.ForeignKey(
        "sales_channels.RemoteProduct",
        on_delete=models.CASCADE,
        related_name="shein_issues",
        help_text="Remote product this issue refers to.",
    )
    version = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Shein submission version associated with this audit result (SPMP...).",
    )
    document_sn = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Shein document serial number for the audit (SPMPA...).",
    )
    spu_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Shein spu_name when available.",
    )
    skc_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Shein skcName/skc_name when available.",
    )
    sku_codes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of sku_code values returned by Shein (when available).",
    )
    audit_state = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Audit state integer returned by webhook notifications.",
    )
    document_state = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Document state integer returned by query-document-state.",
    )
    failed_reason = models.JSONField(
        default=list,
        blank=True,
        help_text="Failure reasons returned by Shein (list of {language, content}).",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True when the issue is currently active.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Last payload used to populate this issue.",
    )

    class Meta:
        verbose_name = "Shein Product Issue"
        verbose_name_plural = "Shein Product Issues"
        ordering = ("remote_product_id", "version", "document_sn")
        constraints = [
            models.UniqueConstraint(
                fields=["remote_product", "version", "document_sn", "skc_name"],
                name="unique_shein_issue_per_submission",
            )
        ]
        search_terms = ("spu_name", "skc_name", "document_sn", "version")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.remote_product_id}:{self.document_sn or self.version or 'unknown'}"

    @classmethod
    def upsert_from_webhook(
        cls,
        *,
        remote_product,
        payload: dict[str, Any],
    ) -> "SheinProductIssue":
        version = str(payload.get("version") or "").strip()
        document_sn = str(payload.get("document_sn") or payload.get("documentSn") or "").strip()
        skc_name = str(payload.get("skc_name") or payload.get("skcName") or "").strip()
        spu_name = str(payload.get("spu_name") or payload.get("spuName") or "").strip()

        sku_codes: list[str] = []
        sku_list = payload.get("sku_list")
        if isinstance(sku_list, list):
            for sku in sku_list:
                if not isinstance(sku, dict):
                    continue
                code = sku.get("sku_code") or sku.get("skuCode")
                if code:
                    sku_codes.append(str(code))

        audit_state: Optional[int]
        try:
            audit_state = int(payload.get("audit_state")) if payload.get("audit_state") is not None else None
        except (TypeError, ValueError):
            audit_state = None

        failed_reason = payload.get("failed_reason")
        if failed_reason is None:
            failed_reason = []
        if not isinstance(failed_reason, list):
            failed_reason = []

        issue, _ = cls.objects.update_or_create(
            remote_product=remote_product,
            version=version,
            document_sn=document_sn,
            skc_name=skc_name,
            defaults={
                "multi_tenant_company": remote_product.multi_tenant_company,
                "spu_name": spu_name,
                "sku_codes": sku_codes,
                "audit_state": audit_state,
                "failed_reason": failed_reason,
                "is_active": bool(failed_reason),
                "raw_data": payload,
            },
        )
        return issue

    @classmethod
    def upsert_from_document_state(
        cls,
        *,
        remote_product,
        record: dict[str, Any],
    ) -> "SheinProductIssue":
        version = str(record.get("version") or "").strip()
        spu_name = str(record.get("spuName") or record.get("spu_name") or "").strip()

        skc_name = str(record.get("skcName") or record.get("skc_name") or "").strip()
        document_sn = str(record.get("documentSn") or record.get("document_sn") or "").strip()

        document_state: Optional[int]
        try:
            document_state = int(record.get("documentState")) if record.get("documentState") is not None else None
        except (TypeError, ValueError):
            document_state = None

        failed_reason = record.get("failedReason") or []
        if not isinstance(failed_reason, list):
            failed_reason = []

        issue, _ = cls.objects.update_or_create(
            remote_product=remote_product,
            version=version,
            document_sn=document_sn,
            skc_name=skc_name,
            defaults={
                "multi_tenant_company": remote_product.multi_tenant_company,
                "spu_name": spu_name,
                "document_state": document_state,
                "failed_reason": failed_reason,
                "is_active": bool(failed_reason),
                "raw_data": record,
            },
        )
        return issue

