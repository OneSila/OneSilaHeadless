"""Import processor for Mirakl schema metadata."""

import logging

from imports_exports.factories.imports import ImportMixin

from sales_channels.integrations.mirakl.factories.sales_channels.full_schema import (
    MiraklFullSchemaSyncFactory,
)


logger = logging.getLogger(__name__)


class MiraklSchemaImportProcessor(ImportMixin):
    """Run the Mirakl schema import using the full schema sync factory."""

    import_rules = True

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(import_process, language)
        self.sales_channel = sales_channel
        self.initial_active = bool(getattr(sales_channel, "active", True))
        self.initial_is_importing = bool(getattr(sales_channel, "is_importing", False))
        self.import_process = self.import_process.get_real_instance()

    def prepare_import_process(self):
        logger.info(
            "Preparing Mirakl schema import channel_id=%s import_id=%s active=%s is_importing=%s",
            self.sales_channel.id,
            self.import_process.id,
            self.initial_active,
            self.initial_is_importing,
        )
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def process_completed(self):
        self.sales_channel.active = self.initial_active
        self.sales_channel.is_importing = self.initial_is_importing
        self.sales_channel.save(update_fields=["active", "is_importing"])
        logger.info(
            "Restored Mirakl schema import channel state channel_id=%s import_id=%s status=%s percentage=%s",
            self.sales_channel.id,
            self.import_process.id,
            self.import_process.status,
            self.import_process.percentage,
        )

    def on_success(self):
        logger.info(
            "Mirakl schema import completed channel_id=%s import_id=%s processed=%s total=%s",
            self.sales_channel.id,
            self.import_process.id,
            self.import_process.processed_records,
            self.import_process.total_records,
        )

    def on_fail(self):
        logger.exception(
            "Mirakl schema import failed channel_id=%s import_id=%s processed=%s total=%s",
            self.sales_channel.id,
            self.import_process.id,
            self.import_process.processed_records,
            self.import_process.total_records,
        )

    def get_total_instances(self):
        return 100

    def import_rules_process(self):
        factory = MiraklFullSchemaSyncFactory(
            sales_channel=self.sales_channel,
            import_process=self.import_process,
        )
        factory.run()
