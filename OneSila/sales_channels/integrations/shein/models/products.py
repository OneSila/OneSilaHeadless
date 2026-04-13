"""Shein integration product models."""

from core import models
from sales_channels.models.products import RemoteEanCode, RemoteProduct, RemoteProductContent
from sales_channels.models import RemoteImageProductAssociation


class SheinProduct(RemoteProduct):
    """Shein remote product model.

    Shein generates a hierarchy of identifiers during publish:
    - SPU: `spu_name` (product container)
    - SKC: `skc_name` (style/color layer)
    - SKU: `sku_code` (sellable unit)
    """

    spu_name = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="SPU identifier returned by publishOrEdit (spu_name).",
    )
    skc_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="SKC identifier returned by publishOrEdit (skc_name).",
    )
    sku_code = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="SKU identifier returned by publishOrEdit (sku_code).",
    )
    pending_external_documents = models.BooleanField(
        default=False,
        help_text="True while this product waits for non-uploadable SHEIN compliance documents to be completed manually.",
    )

    @property
    def url_skc_name(self) -> str | None:
        current_skc_name = str(self.skc_name or "").strip()
        if current_skc_name:
            return current_skc_name

        if self.is_variation:
            return None

        child_variation = (
            self.__class__.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=self,
                is_variation=True,
            )
            .exclude(skc_name__isnull=True)
            .exclude(skc_name="")
            .only("skc_name")
            .first()
        )
        if not child_variation:
            return None

        child_skc_name = str(child_variation.skc_name or "").strip()
        return child_skc_name or None

    def _determine_status(self) -> str:
        if self._has_unresolved_errors():
            return self.STATUS_FAILED
        if self.syncing_current_percentage != 100:
            return self.STATUS_PROCESSING
        if self._has_pending_external_documents():
            return self.STATUS_PENDING_EXTERNAL_DOCUMENTS

        from sales_channels.integrations.shein.helpers.document_state import (
            shein_aggregate_document_states_to_status,
        )

        try:
            from sales_channels.integrations.shein.models import SheinProductIssue

            issue_states = list(
                SheinProductIssue.objects.filter(remote_product=self)
                .exclude(document_state__isnull=True)
                .values_list("document_state", flat=True)
            )
        except Exception:
            issue_states = []

        mapped = shein_aggregate_document_states_to_status(document_states=issue_states)
        has_rejected_documents = self._has_rejected_document_associations()
        has_pending_documents = self._has_pending_document_associations()
        if mapped is not None:
            if has_rejected_documents:
                return self.STATUS_APPROVAL_REJECTED
            if mapped == self.STATUS_COMPLETED and has_pending_documents:
                return self.STATUS_PENDING_APPROVAL
            return mapped

        if has_rejected_documents:
            return self.STATUS_APPROVAL_REJECTED

        if has_pending_documents:
            return self.STATUS_PENDING_APPROVAL

        # After publishOrEdit, Shein products start in review; default to pending approval once we have an SPU.
        if (self.spu_name or self.remote_id):
            return self.STATUS_PENDING_APPROVAL

        return self.STATUS_COMPLETED

    def _has_pending_external_documents(self) -> bool:
        return bool(getattr(self, "pending_external_documents", False))

    def _get_document_status_scope_remote_product_ids(self) -> list[int]:
        if not self.pk:
            return []

        if self.is_variation and self.remote_parent_product_id:
            return list(
                SheinProduct.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_parent_product_id=self.remote_parent_product_id,
                    is_variation=True,
                ).values_list("id", flat=True)
            )

        if self.is_variation:
            return [self.pk]

        variation_ids = list(
            SheinProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=self,
                is_variation=True,
            ).values_list("id", flat=True)
        )
        if variation_ids:
            return variation_ids

        return [self.pk]

    def _has_pending_document_associations(self) -> bool:
        scope_remote_product_ids = self._get_document_status_scope_remote_product_ids()
        if not scope_remote_product_ids:
            return False

        try:
            from sales_channels.integrations.shein.models.documents import (
                SheinDocumentThroughProduct,
            )

            return SheinDocumentThroughProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_product_id__in=scope_remote_product_ids,
                missing_status=SheinDocumentThroughProduct.STATUS_PENDING,
            ).exists()
        except Exception:
            return False

    def _has_rejected_document_associations(self) -> bool:
        scope_remote_product_ids = self._get_document_status_scope_remote_product_ids()
        if not scope_remote_product_ids:
            return False

        try:
            from sales_channels.integrations.shein.models.documents import (
                SheinDocumentThroughProduct,
            )

            return SheinDocumentThroughProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_product_id__in=scope_remote_product_ids,
                missing_status=SheinDocumentThroughProduct.STATUS_REJECTED,
            ).exists()
        except Exception:
            return False


class SheinProductContent(RemoteProductContent):
    """Shein product content model."""
    pass


class SheinEanCode(RemoteEanCode):
    """Shein EAN code model."""
    pass


class SheinImageProductAssociation(RemoteImageProductAssociation):
    """Persist the Shein-transformed image URL for publish payloads."""

    remote_url = models.URLField(
        null=True,
        blank=True,
        help_text="Shein-transformed image URL returned by /open-api/goods/transform-pic.",
    )
    original_url = models.URLField(
        null=True,
        blank=True,
        help_text="Original image URL used for transform-pic (before conversion).",
    )
    image_type = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Shein image type used for transform-pic (1 main, 2 detail, 5 square, 6 color block, 7 detail page).",
    )
    image_group_code = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Shein image_group_code associated with the image set.",
    )

    class Meta:
        verbose_name = "Shein Image Product Association"
        verbose_name_plural = "Shein Image Product Associations"
