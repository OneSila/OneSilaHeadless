"""Import processors for pulling eBay schema information."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

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
        self.category_map: dict[str, dict[str, dict[str, Any]]] | None = None

    def prepare_import_process(self):
        # Prevent push operations during the import and mark the channel as importing.
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.category_map = self.get_category_aspects_map()
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def get_total_instances(self):
        total = sum(len(categories) for categories in self.category_map.values())
        return max(total, 1)

    def import_rules_process(self):
        total = sum(len(categories) for categories in self.category_map.values())

        if total == 0:
            logger.info("No eBay categories found for sales channel %s", self.sales_channel)
            return

        for marketplace_remote_id, categories in self.category_map.items():
            view = EbaySalesChannelView.objects.get(sales_channel=self.sales_channel, remote_id=marketplace_remote_id)

            category_tree_id = view.default_category_tree_id
            if not category_tree_id:
                logger.warning(
                    "Skipping categories for marketplace %s on sales channel %s due to missing default category tree.",
                    marketplace_remote_id,
                    self.sales_channel,
                )
                self.update_percentage(len(categories))
                continue

            for category_id, category_details in categories.items():
                aspects = category_details.get("aspects") if isinstance(category_details, Mapping) else None
                factory = EbayProductTypeRuleFactory(
                    sales_channel=self.sales_channel,
                    view=view,
                    category_id=category_id,
                    category_tree_id=category_tree_id,
                    language=self.language,
                    category_aspects=aspects,
                )
                factory.run()
                self.update_percentage()

    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save(update_fields=["active", "is_importing"])