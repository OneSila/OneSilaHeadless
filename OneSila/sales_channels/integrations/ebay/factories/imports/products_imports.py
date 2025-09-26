"""Async product import scaffolding for the eBay integration."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from imports_exports.factories.imports import AsyncProductImportMixin, ImportMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin


class EbayProductsImportProcessor(ImportMixin, GetEbayAPIMixin):
    """Base processor that will orchestrate eBay product imports."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(import_process, language)

        self.sales_channel = sales_channel
        self.language = language
        self.api = self.get_api()

    def prepare_import_process(self):
        """Placeholder hook executed before the import starts."""

        pass

    def process_completed(self):
        """Placeholder hook executed after the import finishes."""

        pass

    def get_total_instances(self) -> int:
        """Return the number of remote products that will be processed."""

        pass
        return 0

    def get_products_data(self) -> Iterator[dict[str, Any]]:
        """Yield serialized product payloads from the remote API."""

        pass
        return iter(())

    def _parse_prices(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract price payloads from a remote product response."""

        pass
        return []

    def _parse_translations(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract translation payloads from a remote product response."""

        pass
        return []

    def _parse_images(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract image payloads from a remote product response."""

        pass
        return []

    def _parse_variations(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract variation payloads from a remote product response."""

        pass
        return []

    def get_structured_product_data(self, *, product_data: dict[str, Any]) -> dict[str, Any]:
        """Combine parsed sub-sections into the final product payload."""

        pass
        return product_data

    def update_product_log_instance(
        self,
        *,
        log_instance: dict[str, Any],
        import_instance: Any,
    ) -> None:
        """Placeholder hook to update the import log after processing."""

        pass

    def handle_attributes(self, *, import_instance: Any) -> None:
        """Placeholder hook to synchronise product attributes."""

        pass

    def handle_translations(self, *, import_instance: Any) -> None:
        """Placeholder hook to persist product translations."""

        pass

    def handle_prices(self, *, import_instance: Any) -> None:
        """Placeholder hook to persist product prices."""

        pass

    def handle_images(self, *, import_instance: Any) -> None:
        """Placeholder hook to persist product media."""

        pass

    def handle_variations(self, *, import_instance: Any) -> None:
        """Placeholder hook to link variation relationships."""

        pass

    def handle_ean_code(self, *, import_instance: Any) -> None:
        """Placeholder hook to synchronise barcode metadata."""

        pass

    def handle_gtin_exemption(self, *, import_instance: Any) -> None:
        """Placeholder hook to manage GTIN exemption flags."""

        pass

    def handle_product_browse_node(self, *, import_instance: Any) -> None:
        """Placeholder hook to manage browse node assignments."""

        pass

    def handle_sales_channels_views(
        self,
        *,
        import_instance: Any,
        structured_data: dict[str, Any],
    ) -> None:
        """Placeholder hook to link imported products to channel views."""

        pass

    def process_product_item(self, *, product_data: dict[str, Any]) -> None:
        """Process a single serialized product payload."""

        pass


class EbayProductsAsyncImportProcessor(AsyncProductImportMixin, EbayProductsImportProcessor):
    """Async variant of the eBay product import processor."""

    def dispatch_task(self, data, is_last=False, updated_with=None):
        from sales_channels.integrations.ebay.tasks import ebay_product_import_item_task

        task_kwargs = {
            "import_process_id": self.import_process.id,
            "sales_channel_id": self.sales_channel.id,
            "product_data": data,
            "is_last": is_last,
            "updated_with": updated_with,
        }

        ebay_product_import_item_task(**task_kwargs)


class EbayProductItemFactory(EbayProductsImportProcessor):
    """Factory that will handle the import of a single eBay product payload."""

    def __init__(
        self,
        *,
        product_data: dict[str, Any],
        import_process,
        sales_channel,
        is_last: bool = False,
        updated_with: int | None = None,
    ) -> None:
        super().__init__(import_process=import_process, sales_channel=sales_channel)

        self.product_data = product_data
        self.is_last = is_last
        self.updated_with = updated_with

    def run(self) -> None:
        """Execute the product import for the provided payload."""

        pass
