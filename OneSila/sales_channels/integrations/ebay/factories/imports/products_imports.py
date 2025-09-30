"""Async product import scaffolding for the eBay integration."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from typing import Any

from currencies.models import Currency
from imports_exports.factories.imports import AsyncProductImportMixin, ImportMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbayRemoteLanguage
from sales_channels.models import SalesChannelIntegrationPricelist
from sales_prices.models import SalesPrice


def get_parent_skus(*, product_data: Any) -> set[str]:
    """Return the parent SKU identifiers declared on the payload."""

    if not isinstance(product_data, dict):
        return set()

    parent_skus: set[str] = set()

    for key in ("group_ids", "inventory_item_group_keys"):
        values = product_data.get(key)
        if values is None:
            continue

        if isinstance(values, str) or not isinstance(values, (list, tuple, set)):
            iterable = [values]
        else:
            iterable = list(values)

        for value in iterable:
            if value is None:
                continue

            normalized = value.strip() if isinstance(value, str) else str(value)
            if not normalized:
                continue

            parent_skus.add(normalized)

    return parent_skus


def get_is_product_variation(*, product_data: Any) -> tuple[bool, set[str]]:
    """Return whether the payload references a variation and its parent SKUs."""

    parent_skus = get_parent_skus(product_data=product_data)

    return (bool(parent_skus), parent_skus)


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
        """Yield product and offer payload pairs from the remote API."""

        for product in self.get_all_products():
            if not isinstance(product, dict):
                continue

            sku = product.get("sku") or product.get("inventory_item_sku")
            if not sku:
                continue

            offers_iterator = self._paginate_api_results(
                self.api.sell_inventory_get_offers,
                limit=None,
                record_key="record",
                records_key="offers",
                sku=sku,
            )

            for offer in offers_iterator:
                if not isinstance(offer, dict):
                    continue

                yield {"product": product, "offer": offer}

    def import_products_process(self) -> None:
        for product_payload in self.get_products_data():
            if not isinstance(product_payload, dict):
                continue

            product = product_payload.get("product")
            offer = product_payload.get("offer")
            if not isinstance(product, dict):
                continue
            if not isinstance(offer, dict):
                continue

            self.process_product_item(product, offer)
            self.update_percentage()

    def _parse_prices(
        self,
        *,
        product_data: dict[str, Any],
        local_product: Any | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Convert eBay offer pricing into local price and pricelist payloads."""

        if not isinstance(product_data, dict):
            return [], []

        offers_data = product_data.get("offers") or []
        if isinstance(offers_data, list):
            offers = [offer for offer in offers_data if isinstance(offer, dict)]
        elif isinstance(offers_data, dict):
            offers = [offers_data]
        else:
            offers = []

        prices: list[dict[str, Any]] = []
        sales_pricelist_items: list[dict[str, Any]] = []
        processed_currencies: set[str] = set()

        for offer_payload in offers:
            pricing_summary = offer_payload.get("pricing_summary") or {}
            price_data = pricing_summary.get("price") or {}
            amount = price_data.get("value")
            currency_code = price_data.get("currency")

            if amount is None or not currency_code:
                continue

            iso_code = str(currency_code).upper()
            if iso_code in processed_currencies:
                continue

            try:
                price_decimal = Decimal(str(amount))
            except (InvalidOperation, TypeError, ValueError):
                continue

            try:
                currency = Currency.objects.get(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    iso_code=iso_code,
                )
            except Currency.DoesNotExist as exc:
                raise ValueError(
                    f"Currency with ISO code {iso_code} does not exist locally"
                ) from exc

            processed_currencies.add(iso_code)

            scip = (
                SalesChannelIntegrationPricelist.objects.filter(
                    sales_channel=self.sales_channel,
                    price_list__currency=currency,
                )
                .select_related("price_list")
                .first()
            )

            if scip:
                sales_pricelist_items.append(
                    {
                        "salespricelist": scip.price_list,
                        "disable_auto_update": True,
                        "price_auto": price_decimal,
                    }
                )
            else:
                sales_pricelist_items.append(
                    {
                        "salespricelist_data": {
                            "name": f"eBay {self.sales_channel.hostname} {iso_code}",
                            "currency_object": currency,
                        },
                        "disable_auto_update": True,
                        "price_auto": price_decimal,
                    }
                )

            has_sales_price = (
                local_product
                and SalesPrice.objects.filter(
                    product=local_product,
                    currency__iso_code=iso_code,
                ).exists()
            )

            if has_sales_price:
                continue

            price_payload: dict[str, Any] = {
                "price": price_decimal,
                "currency": iso_code,
            }

            original_price = pricing_summary.get("original_retail_price") or {}
            original_amount = original_price.get("value")
            original_currency = original_price.get("currency")

            if original_amount is not None and original_currency:
                try:
                    original_decimal = Decimal(str(original_amount))
                except (InvalidOperation, TypeError, ValueError):
                    original_decimal = None

                if original_decimal is not None and str(original_currency).upper() == iso_code:
                    price_payload["rrp"] = original_decimal

            prices.append(price_payload)

        return prices, sales_pricelist_items

    def _parse_translations(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract translation payloads from a remote product response."""

        if not isinstance(product_data, dict):
            return []

        inventory_item = product_data.get("product")
        if not isinstance(inventory_item, dict):
            inventory_item = product_data
            if not isinstance(inventory_item, dict):
                return []

        locale = inventory_item.get("locale")
        if not isinstance(locale, str) or not locale:
            raise ValueError("Missing locale on eBay inventory item payload")

        remote_language = (
            EbayRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                remote_code__iexact=locale,
            )
            .exclude(local_instance__isnull=True)
            .exclude(local_instance="")
            .first()
        )

        if remote_language is None:
            raise ValueError(
                "Locale %r is not mapped to a local language for sales channel %s"
                % (locale, self.sales_channel.id)
            )

        language_code = remote_language.local_instance

        name = inventory_item.get("title")
        if isinstance(name, str):
            name = name.strip()
            if len(name) > 80:
                name = name[:80]
        else:
            name = None

        subtitle = inventory_item.get("subtitle")
        if isinstance(subtitle, str):
            subtitle = subtitle.strip() or None
        else:
            subtitle = None

        description = inventory_item.get("description")
        if isinstance(description, str):
            description = description.strip()
        else:
            description = None

        listing_description = None
        offers_data = product_data.get("offers")
        if isinstance(offers_data, list):
            offer_iterable = offers_data
        elif isinstance(offers_data, dict):
            offer_iterable = [offers_data]
        else:
            offer_iterable = []

        for offer in offer_iterable:
            if not isinstance(offer, dict):
                continue
            value = offer.get("listing_description")
            if isinstance(value, str) and value.strip():
                listing_description = value.strip()
                break

        if listing_description is None:
            offer = product_data.get("offer")
            if isinstance(offer, dict):
                value = offer.get("listing_description")
                if isinstance(value, str) and value.strip():
                    listing_description = value.strip()

        if listing_description:
            description = listing_description

        if not name:
            return []

        translation: dict[str, Any] = {
            "name": name,
            "language": language_code,
            "subtitle": subtitle,
        }

        if description is not None:
            translation["description"] = description

        return [translation]

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

    def process_product_item(
        self,
        product_data: dict[str, Any],
        offer_data: dict[str, Any] | None = None,
    ) -> None:
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
