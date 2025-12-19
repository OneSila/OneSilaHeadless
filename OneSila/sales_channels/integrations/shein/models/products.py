"""Shein integration product models."""

from core import models
from sales_channels.models.products import RemoteProduct
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

    def _determine_status(self) -> str:
        if self._has_unresolved_errors():
            return self.STATUS_FAILED
        if self.syncing_current_percentage != 100:
            return self.STATUS_PROCESSING

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
        if mapped is not None:
            return mapped

        # After publishOrEdit, Shein products start in review; default to pending approval once we have an SPU.
        if (self.spu_name or self.remote_id):
            return self.STATUS_PENDING_APPROVAL

        return self.STATUS_COMPLETED


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

    class Meta:
        verbose_name = "Shein Image Product Association"
        verbose_name_plural = "Shein Image Product Associations"
