"""Import processors for pulling eBay schema information."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from imports_exports.factories.imports import ImportMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.factories.sales_channels.full_schema import (
    EbayProductTypeRuleFactory,
)
from sales_channels.integrations.ebay.models import EbaySalesChannelView

logger = logging.getLogger(__name__)


class EbaySchemaImportProcessor(ImportMixin, GetEbayAPIMixin):
    """Import processor that orchestrates schema synchronization for eBay."""

    import_properties = False
    import_select_values = False
    import_rules = True
    import_products = False

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)

        self.sales_channel = sales_channel
        self.initial_sales_channel_status = sales_channel.active
        self.api = self.get_api()

        self._category_map: dict[str, set[str]] | None = None

    def prepare_import_process(self):
        # Prevent push operations during the import and mark the channel as importing.
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def get_total_instances(self):
        self._ensure_category_map()
        category_map = self._category_map or {}
        total = sum(len(category_ids) for category_ids in category_map.values())
        return max(total, 1)

    def import_rules_process(self):
        self._ensure_category_map()
        category_map = self._category_map or {}
        total = sum(len(category_ids) for category_ids in category_map.values())
        self.total_import_instances_cnt = max(total, 1)
        self.set_threshold_chunk()

        if total == 0:
            logger.info("No eBay categories found for sales channel %s", self.sales_channel)
            return

        for marketplace_remote_id, category_ids in category_map.items():
            view = (
                EbaySalesChannelView.objects
                .filter(sales_channel=self.sales_channel, remote_id=marketplace_remote_id)
                .first()
            )
            if view is None:
                logger.warning(
                    "Skipping categories for marketplace %s on sales channel %s because the view is missing.",
                    marketplace_remote_id,
                    self.sales_channel,
                )
                self.update_percentage(len(category_ids))
                continue

            real_view_getter = getattr(view, "get_real_instance", None)
            if callable(real_view_getter):
                real_view = real_view_getter()
                if isinstance(real_view, EbaySalesChannelView):
                    view = real_view

            category_tree_id = getattr(view, "default_category_tree_id", None)
            if not category_tree_id:
                logger.warning(
                    "Skipping categories for marketplace %s on sales channel %s due to missing default category tree.",
                    marketplace_remote_id,
                    self.sales_channel,
                )
                self.update_percentage(len(category_ids))
                continue

            for category_id in sorted(category_ids):
                factory = EbayProductTypeRuleFactory(
                    sales_channel=self.sales_channel,
                    view=view,
                    category_id=category_id,
                    category_tree_id=category_tree_id,
                    language=self.language,
                )
                factory.run()
                self.update_percentage()

    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def _ensure_category_map(self) -> None:
        if self._category_map is not None:
            return

        try:
            raw_category_map = self.get_all_category_ids()
        except Exception:  # pragma: no cover - defensive logging
            logger.exception(
                "Unable to fetch category identifiers for eBay sales channel %s",
                self.sales_channel,
            )
            raw_category_map = {}

        normalized: dict[str, set[str]] = {}
        if isinstance(raw_category_map, Mapping):
            for marketplace_remote_id, category_ids in raw_category_map.items():
                if not marketplace_remote_id or not category_ids:
                    continue

                marketplace_key = str(marketplace_remote_id)
                normalized_categories = {
                    str(category_id)
                    for category_id in category_ids
                    if category_id is not None and category_id != ""
                }

                if normalized_categories:
                    normalized[marketplace_key] = normalized_categories

        self._category_map = normalized
