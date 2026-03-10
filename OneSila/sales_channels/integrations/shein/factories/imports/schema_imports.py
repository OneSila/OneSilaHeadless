"""Import processors for pulling Shein schema metadata."""

import logging
from typing import Optional

from core.mixins import TemporaryDisableInspectorSignalsMixin
from imports_exports.factories.imports import ImportMixin
from products_inspector.models import Inspector
from sales_channels.integrations.shein.factories.sales_channels.full_schema import (
    SheinCategoryTreeSyncFactory,
)
from sales_channels.integrations.shein.models import SheinProductCategory, SheinSalesChannel


logger = logging.getLogger(__name__)


class SheinSchemaImportProcessor(TemporaryDisableInspectorSignalsMixin, ImportMixin):
    """Simple schema import that reuses the full category tree synchronisation factory."""

    import_rules = True

    def __init__(
        self,
        import_process,
        sales_channel: SheinSalesChannel,
        language: Optional[str] = None,
    ) -> None:
        super().__init__(import_process, language)
        self.sales_channel = sales_channel
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self.initial_active = bool(getattr(sales_channel, "active", True))
        self.initial_is_importing = bool(getattr(sales_channel, "is_importing", False))
        self.import_process = self.import_process.get_real_instance()

    def prepare_import_process(self) -> None:
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def process_completed(self) -> None:
        self.sales_channel.active = self.initial_active
        self.sales_channel.is_importing = self.initial_is_importing
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def refresh_inspector_status(self, *, run_inspection: bool = True) -> None:
        from products_inspector.signals import inspector_block_refresh

        if self._original_inspector_send is not None:
            inspector_block_refresh.send = self._original_inspector_send
            self._original_inspector_send = None

        if not run_inspection:
            self.skipped_inspector_sku = getattr(self, "skipped_inspector_sku", set())
            return

        product_ids = (
            SheinProductCategory.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
            )
            .values_list("product_id", flat=True)
            .distinct()
        )

        inspectors = Inspector.objects.filter(product_id__in=product_ids).select_related("product")
        for inspector in inspectors.iterator():
            inspector.inspect_product(run_async=False)

    def get_total_instances(self) -> int:
        return 100

    def import_rules_process(self) -> None:
        channel_id = getattr(self.sales_channel, "pk", None)
        language = self.language or "auto"

        logger.info(
            "Starting Shein schema import for channel=%s language=%s",
            channel_id,
            language,
        )

        factory = SheinCategoryTreeSyncFactory(
            sales_channel=self.sales_channel,
            language=self.language,
            import_process=self.import_process,
            sync_document_types=True,
        )
        factory.run()

        logger.info(
            (
                "Completed Shein schema import for channel=%s: "
                "%s categories, %s product types, %s cert-rules, %s document types created, %s updated"
            ),
            channel_id,
            len(factory.synced_categories),
            len(factory.synced_product_types),
            factory.synced_document_rules,
            factory.synced_document_types_created,
            factory.synced_document_types_updated,
        )
