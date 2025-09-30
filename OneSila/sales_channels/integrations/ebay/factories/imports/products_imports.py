"""Async product import scaffolding for the eBay integration."""

from __future__ import annotations

import logging
import traceback

from collections.abc import Iterator, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any
from django.db import IntegrityError
from django.db.models import Q
from properties.models import Property
from products.product_types import CONFIGURABLE, SIMPLE

from currencies.models import Currency
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.helpers import append_broken_record
from core.helpers import ensure_serializable
from sales_channels.integrations.ebay.constants import EBAY_INTERNAL_PROPERTY_DEFAULTS
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.helpers import get_is_product_variation
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
    EbayProductType,
    EbayRemoteLanguage,
    EbayMediaThroughProduct,
    EbayPrice,
    EbayProductContent,
    EbayEanCode,
)
from sales_channels.models import SalesChannelIntegrationPricelist
from sales_prices.models import SalesPrice
from sales_channels.factories.imports import SalesChannelImportMixin

logger = logging.getLogger(__name__)


class EbayProductsImportProcessor(SalesChannelImportMixin, GetEbayAPIMixin):
    """Base processor that will orchestrate eBay product imports."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_BROKEN_IMPORT_PROCESS = "BROKEN_IMPORT_PROCESS"
    ERROR_MISSING_MARKETPLACE = "MISSING_MARKETPLACE"
    ERROR_PARENT_FETCH_FAILED = "PARENT_FETCH_FAILED"
    ERROR_INVALID_PRODUCT_DATA = "INVALID_PRODUCT_DATA"

    remote_ean_code_class = EbayEanCode
    remote_product_content_class = EbayProductContent
    remote_imageproductassociation_class = EbayMediaThroughProduct
    remote_price_class = EbayPrice

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(
            import_process=import_process,
            sales_channel=sales_channel,
            language=language,
        )

        self.language = language
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self._processed_parent_skus: set[str] = set()

    def _add_broken_record(
        self,
        *,
        code: str,
        message: str,
        data: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "code": code,
            "message": message,
            "data": ensure_serializable(data) if data else {},
            "context": context or {},
        }

        if exc is not None:
            record["error"] = str(exc)
            record["traceback"] = traceback.format_exc()

        append_broken_record(self.import_process.id, record)

    def get_total_instances(self) -> int:
        """Return the number of remote products that will be processed."""

        return self.get_products_count()

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

    def get_product_rule(
        self,
        *,
        offer_data: dict[str, Any] | None = None,
    ) -> Any | None:
        """Return the local product rule linked to the offer's category."""

        if not isinstance(offer_data, dict):
            return None

        category_id = offer_data.get("category_id")
        marketplace_id = offer_data.get("marketplace_id")

        if category_id is None or not marketplace_id:
            return None

        category_key = str(category_id).strip()
        marketplace_key = str(marketplace_id).strip()

        if not category_key or not marketplace_key:
            return None

        product_type = (
            EbayProductType.objects.filter(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                marketplace__remote_id=marketplace_key,
                remote_id=category_key,
            )
            .select_related("local_instance")
            .first()
        )

        if not product_type or product_type.local_instance is None:
            return None

        return product_type.local_instance

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
        offer_data: dict[str, Any],
        local_product: Any | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Convert eBay offer pricing into local price and pricelist payloads."""

        if not isinstance(offer_data, dict):
            return [], []

        pricing_summary = offer_data.get("pricing_summary") or {}
        if not isinstance(pricing_summary, Mapping):
            pricing_summary = {}

        price_data = pricing_summary.get("price") or {}
        if not isinstance(price_data, Mapping):
            price_data = {}

        amount = price_data.get("value")
        currency_code = price_data.get("currency")

        if amount is None or not currency_code:
            return [], []

        iso_code = str(currency_code).upper()

        try:
            price_decimal = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            return [], []

        try:
            currency = Currency.objects.get(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                iso_code=iso_code,
            )
        except Currency.DoesNotExist as exc:
            raise ValueError(
                f"Currency with ISO code {iso_code} does not exist locally"
            ) from exc

        sales_pricelist_items: list[dict[str, Any]] = []

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

        prices: list[dict[str, Any]] = []

        has_sales_price = (
            local_product
            and SalesPrice.objects.filter(
                product=local_product,
                currency__iso_code=iso_code,
            ).exists()
        )

        if not has_sales_price:
            price_payload: dict[str, Any] = {
                "price": price_decimal,
                "currency": iso_code,
            }

            original_price = pricing_summary.get("original_retail_price") or {}
            if not isinstance(original_price, Mapping):
                original_price = {}

            original_amount = original_price.get("value")
            original_currency = original_price.get("currency")

            if original_amount is not None and original_currency:
                try:
                    original_decimal = Decimal(str(original_amount))
                except (InvalidOperation, TypeError, ValueError):
                    original_decimal = None

                if (
                    original_decimal is not None
                    and str(original_currency).upper() == iso_code
                ):
                    price_payload["rrp"] = original_decimal

            prices.append(price_payload)

        return prices, sales_pricelist_items

    def _parse_translations(
        self,
        *,
        product_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Extract translation payloads and detected language."""

        if not isinstance(product_data, dict):
            return [], None

        inventory_item = product_data.get("product")
        if not isinstance(inventory_item, dict):
            inventory_item = product_data
            if not isinstance(inventory_item, dict):
                return [], None

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
            return [], language_code

        translation: dict[str, Any] = {
            "name": name,
            "language": language_code,
            "subtitle": subtitle,
        }

        if description is not None:
            translation["description"] = description

        return [translation], language_code

    def _parse_images(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract image payloads from a remote product response."""

        if not isinstance(product_data, dict):
            return []

        product_payload = product_data.get("product") or {}
        if not isinstance(product_payload, dict):
            return []

        image_urls = product_payload.get("image_urls")
        if not image_urls:
            return []

        if isinstance(image_urls, str) or not isinstance(image_urls, (list, tuple, set)):
            iterable = [image_urls]
        else:
            iterable = list(image_urls)

        images: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for value in iterable:
            if value is None:
                continue

            url = str(value).strip()
            if not url or url in seen_urls:
                continue

            sort_order = len(images)
            images.append(
                {
                    "image_url": url,
                    "sort_order": sort_order,
                    "is_main_image": sort_order == 0,
                }
            )
            seen_urls.add(url)

        return images

    def _parse_attributes(
        self,
        *,
        product_data: dict[str, Any],
        view: EbaySalesChannelView | None = None,
    ) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
        """Extract attribute payloads and mirror data for the given product."""

        attributes: list[dict[str, Any]] = []
        mirror_map: dict[int, dict[str, Any]] = {}

        if not isinstance(product_data, dict):
            return attributes, mirror_map

        product_section = product_data.get("product")
        if not isinstance(product_section, Mapping):
            product_section = {}

        package_weight_size = product_data.get("packageWeightAndSize")
        if not isinstance(package_weight_size, Mapping):
            package_weight_size = {}

        dimensions = package_weight_size.get("dimensions")
        if not isinstance(dimensions, Mapping):
            dimensions = {}

        weight = package_weight_size.get("weight")
        if not isinstance(weight, Mapping):
            weight = {}

        internal_defaults_map = {definition["code"]: definition for definition in EBAY_INTERNAL_PROPERTY_DEFAULTS}
        internal_codes = list(internal_defaults_map.keys())

        existing_internal = {
            internal_property.code: internal_property
            for internal_property in EbayInternalProperty.objects.filter(
                sales_channel=self.sales_channel,
                code__in=internal_codes,
            )
        }

        internal_properties: dict[str, EbayInternalProperty] = {}
        for code in internal_codes:
            internal_property = existing_internal.get(code)
            if internal_property is None:
                definition = internal_defaults_map[code]
                internal_property, _ = EbayInternalProperty.objects.get_or_create(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    code=code,
                    defaults={
                        "name": definition["name"],
                        "type": definition["type"],
                        "is_root": definition["is_root"],
                    },
                )
            internal_properties[code] = internal_property

        def _normalize_single(value: Any) -> Any:
            if isinstance(value, (list, tuple, set)):
                for entry in value:
                    normalized = _normalize_single(entry)
                    if normalized not in (None, ""):
                        return normalized
                return None
            if isinstance(value, str):
                stripped = value.strip()
                return stripped or None
            if isinstance(value, Mapping):
                return None
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                return value
            if value is None:
                return None
            return str(value)

        internal_values: dict[str, Any] = {
            "condition": _normalize_single(product_data.get("condition")),
            "brand": _normalize_single(product_section.get("brand")),
            "mpn": _normalize_single(product_section.get("mpn")),
            "upc": _normalize_single(product_section.get("upc")),
            "isbn": _normalize_single(product_section.get("isbn")),
            "epid": _normalize_single(product_section.get("epid")),
            "packageWeightAndSize__dimensions__length": _normalize_single(dimensions.get("length")),
            "packageWeightAndSize__dimensions__width": _normalize_single(dimensions.get("width")),
            "packageWeightAndSize__dimensions__height": _normalize_single(dimensions.get("height")),
            "packageWeightAndSize__weight__value": _normalize_single(weight.get("value")),
            "packageWeightAndSize__packageType": _normalize_single(package_weight_size.get("packageType")),
            "packageWeightAndSize__shippingIrregular": _normalize_single(package_weight_size.get("shippingIrregular")),
        }

        for code, value in internal_values.items():
            if value in (None, ""):
                continue

            internal_property = internal_properties.get(code)
            if not internal_property or not internal_property.local_instance:
                continue

            attributes.append({
                "property": internal_property.local_instance,
                "value": value,
            })

        aspect_payload: dict[str, Any]
        if "product" in product_data and isinstance(product_data["product"], Mapping):
            aspect_payload = product_data
        else:
            aspect_payload = {"product": product_section}

        aspects_map = self._extract_product_aspects(product=aspect_payload)

        if not aspects_map:
            return attributes, mirror_map

        for aspect_name, values in aspects_map.items():
            if not aspect_name or not values:
                continue

            normalized_values = sorted({str(value) for value in values if value not in (None, "")})
            if not normalized_values:
                continue

            property_filters = {
                "sales_channel": self.sales_channel,
            }
            if isinstance(view, EbaySalesChannelView):
                property_filters["marketplace"] = view

            remote_property = EbayProperty.objects.filter(**property_filters).filter(
                Q(localized_name__iexact=aspect_name) | Q(translated_name__iexact=aspect_name)
            ).first()

            if not remote_property or not remote_property.local_instance:
                continue

            property_instance = remote_property.local_instance
            marketplace = view or remote_property.marketplace

            remote_value: Any | None = None
            remote_select_value: EbayPropertySelectValue | None = None
            remote_select_values: list[EbayPropertySelectValue] = []
            is_mapped = False

            if property_instance.type == Property.TYPES.SELECT:
                remote_value = normalized_values[0]
                if marketplace is None:
                    select_value = None
                else:
                    select_value, _ = EbayPropertySelectValue.objects.get_or_create(
                        multi_tenant_company=self.sales_channel.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        marketplace=marketplace,
                        ebay_property=remote_property,
                        localized_value=remote_value,
                        defaults={"translated_value": remote_value},
                    )

                if select_value is not None:
                    remote_select_value = select_value
                    remote_select_values = [select_value]
                    if select_value.local_instance:
                        is_mapped = True
                        attributes.append(
                            {
                                "property": property_instance,
                                "value": select_value.local_instance.id,
                                "value_is_id": True,
                            }
                        )

            elif property_instance.type == Property.TYPES.MULTISELECT:
                remote_value = normalized_values
                if marketplace is not None:
                    mapped_ids: list[int] = []
                    for value_entry in normalized_values:
                        select_value, _ = EbayPropertySelectValue.objects.get_or_create(
                            multi_tenant_company=self.sales_channel.multi_tenant_company,
                            sales_channel=self.sales_channel,
                            marketplace=marketplace,
                            ebay_property=remote_property,
                            localized_value=value_entry,
                            defaults={"translated_value": value_entry},
                        )
                        remote_select_values.append(select_value)
                        if select_value.local_instance:
                            mapped_ids.append(select_value.local_instance.id)

                    if mapped_ids and len(mapped_ids) == len(normalized_values):
                        is_mapped = True
                        attributes.append(
                            {
                                "property": property_instance,
                                "value": mapped_ids,
                                "value_is_id": True,
                            }
                        )

            else:
                remote_value = normalized_values[0]
                is_mapped = True
                attributes.append(
                    {
                        "property": property_instance,
                        "value": remote_value,
                    }
                )

            if remote_value is None and not remote_select_values:
                continue

            mirror_map[property_instance.id] = {
                "remote_property": remote_property,
                "remote_value": remote_value,
                "is_mapped": is_mapped,
                "remote_select_value": remote_select_value,
                "remote_select_values": remote_select_values,
            }

        return attributes, mirror_map

    def _parse_configurator_select_values(
        self,
        *,
        product_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return configurator select values declared on the remote payload."""

        if not isinstance(product_data, dict):
            return []

        varies_by = product_data.get("varies_by")
        if not isinstance(varies_by, dict):
            return []

        specifications = varies_by.get("specifications")
        if specifications is None:
            return []

        if isinstance(specifications, dict):
            raw_specs = [specifications]
        elif isinstance(specifications, (list, tuple, set)):
            raw_specs = [spec for spec in specifications if isinstance(spec, dict)]
        else:
            return []

        configurator_values: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for spec in raw_specs:
            name = spec.get("name")
            if not isinstance(name, str):
                continue

            normalized_name = name.strip()
            if not normalized_name:
                continue

            normalized_key = normalized_name.casefold()
            if normalized_key in seen_names:
                continue

            seen_names.add(normalized_key)

            remote_property = (
                EbayProperty.objects.filter(
                    sales_channel=self.sales_channel,
                )
                .filter(localized_name__iexact=normalized_name)
                .select_related("local_instance")
                .first()
            )

            if remote_property and remote_property.local_instance:
                configurator_values.append({"property": remote_property.local_instance})
                continue

            configurator_values.append(
                {
                    "property_data": {
                        "name": normalized_name,
                        "type": Property.TYPES.SELECT,
                    }
                }
            )

        return configurator_values

    def _extract_sku(self, payload: Any) -> str | None:
        if not isinstance(payload, Mapping):
            return None

        for key in ("sku", "inventory_item_sku", "inventoryItemSku"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        product_section = payload.get("product")
        if isinstance(product_section, Mapping):
            sku_value = product_section.get("sku")
            if isinstance(sku_value, str) and sku_value.strip():
                return sku_value.strip()

        for key in ("inventory_item_group_key", "inventoryItemGroupKey"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    def _extract_group_inventory_items(
        self,
        response: Any,
        *,
        exclude_sku: str | None = None,
    ) -> list[dict[str, Any]]:
        items: list[tuple[str | None, dict[str, Any]]] = []

        def _collect(candidate: Any) -> None:
            if isinstance(candidate, Mapping):
                sku = self._extract_sku(candidate)
                if sku or "product" in candidate:
                    items.append((sku, dict(candidate)))
                for key in (
                    "inventory_items",
                    "inventoryItems",
                    "members",
                    "inventory_item_group",
                    "inventoryItemGroup",
                ):
                    nested = candidate.get(key)
                    if nested is not None:
                        _collect(nested)
            elif isinstance(candidate, (list, tuple, set)):
                for entry in candidate:
                    _collect(entry)

        _collect(response)

        unique_items: list[dict[str, Any]] = []
        seen_skus: set[str] = set()
        excluded = exclude_sku.strip() if isinstance(exclude_sku, str) else None

        for sku, payload in items:
            normalized = sku.strip() if isinstance(sku, str) else None
            if normalized and excluded and normalized == excluded:
                continue
            key = normalized or str(id(payload))
            if key in seen_skus:
                continue
            seen_skus.add(key)
            unique_items.append(payload)

        return unique_items

    def get__product_data(
        self,
        *,
        product_data: dict[str, Any],
        offer_data: dict[str, Any],
        is_variation: bool,
        is_configurable: bool,
        product_instance: Any | None = None,
    ) -> tuple[dict[str, Any], str | None, EbaySalesChannelView | None]:
        """Return the structured payload, language, and view for an eBay product."""

        if not isinstance(product_data, dict):
            product_data = {}

        normalized_product = dict(product_data)

        product_section = normalized_product.get("product")
        if not isinstance(product_section, Mapping):
            product_section = normalized_product
            normalized_product["product"] = product_section

        if isinstance(offer_data, dict):
            normalized_product.setdefault("offer", offer_data)
            normalized_product.setdefault("offers", [offer_data])
        else:
            offer_data = {}

        sku = normalized_product.get("sku") or normalized_product.get("inventory_item_sku")
        if not sku and isinstance(product_section, Mapping):
            sku = product_section.get("sku")

        if not sku:
            raise ValueError("Missing SKU on eBay inventory item payload")

        sku = str(sku).strip()

        title = None
        if isinstance(product_section, Mapping):
            raw_title = product_section.get("title")
            if isinstance(raw_title, str):
                title = raw_title.strip()
                if len(title) > 80:
                    title = title[:80]

        if not title:
            title = sku

        listing_data = offer_data.get("listing") if isinstance(offer_data, Mapping) else {}
        if not isinstance(listing_data, Mapping):
            listing_data = {}

        listing_status = listing_data.get("listing_status")
        is_active = bool(listing_status and str(listing_status).upper() == "ACTIVE")

        marketplace_id = offer_data.get("marketplace_id") if isinstance(offer_data, Mapping) else None
        if marketplace_id is not None:
            marketplace_id = str(marketplace_id).strip()
        if not marketplace_id:
            raise ValueError("Missing marketplace_id in eBay offer payload")

        view = (
            EbaySalesChannelView.objects.filter(
                sales_channel=self.sales_channel,
                remote_id=marketplace_id,
            )
            .select_related()
            .first()
        )

        if view is None:
            raise ValueError(
                f"Marketplace {marketplace_id} is not linked to sales channel {self.sales_channel.id}"
            )

        structured: dict[str, Any] = {
            "sku": sku,
            "name": title,
            "active": is_active,
            "type": CONFIGURABLE if is_configurable else SIMPLE,
        }

        images = self._parse_images(product_data=normalized_product)
        if images:
            structured["images"] = images

        if not is_configurable:
            prices, sales_pricelist_items = self._parse_prices(
                offer_data=offer_data,
                local_product=product_instance,
            )
            if prices:
                structured["prices"] = prices
            if sales_pricelist_items:
                structured["sales_pricelist_items"] = sales_pricelist_items

        attributes, mirror_map = self._parse_attributes(
            product_data=normalized_product,
            view=view,
        )

        if attributes:
            structured["properties"] = attributes
            structured["__mirror_product_properties_map"] = mirror_map

        translations, language = self._parse_translations(
            product_data=normalized_product,
        )
        if translations:
            structured["translations"] = translations

        if is_configurable:
            configurator_values = self._parse_configurator_select_values(
                product_data=normalized_product,
            )
            if configurator_values:
                structured["configurator_select_values"] = configurator_values

        structured["__marketplace_id"] = marketplace_id

        return structured, language, view


    def handle_attributes(self, *, import_instance: Any) -> None:
        """Placeholder hook to synchronise product attributes."""

        pass

    def handle_variations(self, *, import_instance: Any) -> None:
        """Placeholder hook to link variation relationships."""

        pass

    def handle_sales_channels_views(
        self,
        *,
        import_instance: Any,
        structured_data: dict[str, Any],
        view: EbaySalesChannelView | None = None,
        offer_data: dict[str, Any] | None = None,
        child_offer_data: dict[str, Any] | None = None,
    ) -> None:
        """Placeholder hook to link imported products to channel views."""

        pass

    def process_product_item(
        self,
        product_data: dict[str, Any],
        offer_data: dict[str, Any] | None = None,
        child_offer_data: dict[str, Any] | None = None,
    ) -> None:
        """Process a single serialized product payload."""

        if not isinstance(product_data, dict):
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="Invalid product payload received",
                data={"raw": product_data},
            )
            return

        sku = self._extract_sku(product_data)
        if not sku:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="Unable to determine SKU for inventory item",
                data=product_data,
            )
            return

        sku = sku.strip()

        remote_product = (
            EbayProduct.objects.filter(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
                remote_sku=sku,
            )
            .select_related("local_instance")
            .first()
        )
        product_instance = remote_product.local_instance if remote_product and remote_product.local_instance else None

        is_variation, parent_skus = get_is_product_variation(product_data=product_data)

        if remote_product:
            is_variation = remote_product.is_variation

        if parent_skus and child_offer_data is None:
            for parent_sku in parent_skus:
                normalized_parent = parent_sku.strip() if isinstance(parent_sku, str) else str(parent_sku)
                if not normalized_parent:
                    continue
                if normalized_parent == sku or normalized_parent in self._processed_parent_skus:
                    continue

                self._processed_parent_skus.add(normalized_parent)

                try:
                    group_response = self.api.sell_inventory_get_inventory_item_group(
                        inventory_item_group_key=normalized_parent,
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning(
                        "Failed to fetch inventory item group %s for SKU %s", normalized_parent, sku, exc_info=exc
                    )
                    self._add_broken_record(
                        code=self.ERROR_PARENT_FETCH_FAILED,
                        message="Unable to fetch parent inventory item group",
                        data={"sku": sku, "parent_sku": normalized_parent},
                        exc=exc,
                    )
                    continue

                parent_items = self._extract_group_inventory_items(
                    group_response,
                    exclude_sku=sku,
                )

                if not parent_items:
                    self._add_broken_record(
                        code=self.ERROR_PARENT_FETCH_FAILED,
                        message="Parent inventory group returned no items",
                        data={"sku": sku, "parent_sku": normalized_parent},
                    )
                    continue

                for parent_item in parent_items:
                    self.process_product_item(parent_item, child_offer_data=offer_data)

        active_offer = offer_data if isinstance(offer_data, dict) else None
        if active_offer is None and isinstance(child_offer_data, dict):
            active_offer = child_offer_data

        if active_offer is None:
            self._add_broken_record(
                code=self.ERROR_MISSING_MARKETPLACE,
                message="Missing offer data to determine marketplace",
                data={"sku": sku},
            )
            return

        is_parent_product = child_offer_data is not None and not is_variation
        is_configurable = bool(is_parent_product)

        rule = None
        if remote_product and remote_product.local_instance:
            existing_rule = remote_product.local_instance.get_product_rule()
            if existing_rule:
                rule = existing_rule

        if rule is None:
            rule = self.get_product_rule(offer_data=active_offer)

        try:
            structured, language, view = self.get__product_data(
                product_data=product_data,
                offer_data=active_offer,
                is_variation=is_variation,
                is_configurable=is_configurable,
                product_instance=product_instance,
            )
        except ValueError as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message=str(exc) or "Invalid product data returned by eBay",
                data={"sku": sku},
                context={"is_variation": is_variation},
                exc=exc,
            )
            return

        if remote_product and remote_product.local_instance and remote_product.local_instance.type:
            structured["type"] = remote_product.local_instance.type

        try:
            sku_for_defaults = structured["sku"]
        except KeyError:
            sku_for_defaults = sku

        instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=rule,
            sales_channel=self.sales_channel,
            instance=product_instance,
            update_current_rule=True,
        )

        if instance.data.get("type") != CONFIGURABLE:
            instance.update_only = True

        instance.prepare_mirror_model_class(
            mirror_model_class=EbayProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={
                "remote_sku": sku_for_defaults,
                "is_variation": is_variation,
            },
        )
        instance.language = language

        try:
            instance.process()
        except IntegrityError as exc:
            context = {
                "sku": instance.data.get("sku", sku),
                "marketplace_id": instance.data.get("__marketplace_id"),
                "is_variation": is_variation,
            }
            self._add_broken_record(
                code=self.ERROR_BROKEN_IMPORT_PROCESS,
                message="Broken import process for SKU",
                data=instance.data,
                context=context,
                exc=exc,
            )

            if remote_product:
                instance.remote_instance = remote_product
                if product_instance:
                    instance.instance = product_instance
            else:
                return

        if instance.remote_instance is None:
            instance.remote_instance = remote_product

        if instance.remote_instance is None:
            self._add_broken_record(
                code=self.ERROR_BROKEN_IMPORT_PROCESS,
                message="Remote instance missing after processing",
                data=instance.data,
                context={"sku": instance.data.get("sku", sku)},
            )
            return

        self.update_remote_product(instance, product_data, view, is_variation)

        if not is_parent_product:
            self.handle_ean_code(import_instance=instance)
            self.handle_translations(import_instance=instance)
            self.handle_prices(import_instance=instance)
            self.handle_images(import_instance=instance)

        if instance.data.get("type") == CONFIGURABLE:
            self.handle_variations(import_instance=instance)

        if not is_variation:
            self.handle_sales_channels_views(
                import_instance=instance,
                structured_data=instance.data,
                view=view,
                offer_data=active_offer,
                child_offer_data=child_offer_data,
            )


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
