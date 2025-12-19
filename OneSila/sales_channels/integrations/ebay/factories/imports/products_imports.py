"""Async product import scaffolding for the eBay integration."""

from __future__ import annotations

import logging
import traceback

from collections.abc import Iterator, Mapping
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q

from core.mixins import TemporaryDisableInspectorSignalsMixin
from properties.models import Property, ProductProperty
from products.product_types import CONFIGURABLE, SIMPLE

from currencies.models import Currency
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.helpers import append_broken_record, increment_processed_records
from core.helpers import ensure_serializable
from sales_channels.integrations.ebay.constants import EBAY_INTERNAL_PROPERTY_DEFAULTS
from ebay_rest.error import Error as EbayAPIError
from sales_channels.integrations.ebay.exceptions import EbayTemporarySystemError
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.helpers import get_is_product_variation
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbayProductOffer,
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
    EbayProductType,
    EbayRemoteLanguage,
    EbayMediaThroughProduct,
    EbayPrice,
    EbayProductContent,
    EbayEanCode, EbayProductProperty, EbayProductCategory,
)
from sales_channels.models import SalesChannelIntegrationPricelist, SalesChannelViewAssign
from sales_prices.models import SalesPrice
from sales_channels.factories.imports import SalesChannelImportMixin
from sales_channels.models.products import RemoteProductConfigurator

logger = logging.getLogger(__name__)


class _HtmlClassExtractor(HTMLParser):
    """Utility parser that captures the first element matching a CSS class."""

    def __init__(self, target_class: str) -> None:
        super().__init__(convert_charrefs=False)
        self._target_class = target_class.casefold()
        self._capture_depth = 0
        self._buffer: list[str] = []
        self._completed = False

    def _has_target_class(self, attrs: list[tuple[str, str | None]]) -> bool:
        for attr_name, attr_value in attrs:
            if attr_name and attr_name.casefold() == "class" and attr_value:
                classes = {
                    chunk.strip().casefold()
                    for chunk in attr_value.split()
                    if chunk and chunk.strip()
                }
                if self._target_class in classes:
                    return True
        return False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._completed:
            return

        if self._capture_depth > 0:
            self._capture_depth += 1
            self._buffer.append(self.get_starttag_text())
            return

        if self._has_target_class(attrs):
            self._capture_depth = 1
            self._buffer.append(self.get_starttag_text())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._completed:
            return

        if self._capture_depth > 0:
            self._buffer.append(self.get_starttag_text())
            return

        if self._has_target_class(attrs):
            self._buffer.append(self.get_starttag_text())
            self._completed = True

    def handle_endtag(self, tag: str) -> None:
        if self._capture_depth == 0:
            return

        self._buffer.append(f"</{tag}>")
        self._capture_depth -= 1
        if self._capture_depth == 0:
            self._completed = True

    def handle_data(self, data: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        if self._capture_depth > 0:
            self._buffer.append(f"<?{data}>")

    def get_content(self) -> str | None:
        if not self._buffer:
            return None
        return "".join(self._buffer)


class EbayProductsImportProcessor(TemporaryDisableInspectorSignalsMixin, SalesChannelImportMixin, GetEbayAPIMixin):
    """Base processor that will orchestrate eBay product imports."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_BROKEN_IMPORT_PROCESS = "BROKEN_IMPORT_PROCESS"
    ERROR_MISSING_MARKETPLACE = "MISSING_MARKETPLACE"
    ERROR_PARENT_FETCH_FAILED = "PARENT_FETCH_FAILED"
    ERROR_INVALID_PRODUCT_DATA = "INVALID_PRODUCT_DATA"
    ERROR_INVALID_CATEGORY_ASSIGNMENT = "INVALID_CATEGORY_ASSIGNMENT"

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
        self._content_class_filter = self._normalize_content_class(
            getattr(self.import_process, "content_class", None)
        )
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self._processed_parent_skus: set[str] = set()
        self._parent_child_sku_map: dict[str, set[str]] = {}

    @staticmethod
    def _normalize_content_class(value: Any | None) -> str | None:
        if not isinstance(value, str):
            return None

        normalized = value.strip()
        if normalized.startswith("."):
            normalized = normalized[1:]
        normalized = normalized.strip()

        return normalized or None

    @staticmethod
    def _unescape_description_html(*, description: str) -> str:
        """Decode escaped HTML fragments returned as JSON-safe strings."""

        if "\\'" not in description and '\\"' not in description:
            return description

        try:
            return description.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:  # pragma: no cover - defensive
            logger.debug("Failed to unescape eBay description", exc_info=True)
            return description

    def _filter_description_by_content_class(self, description: str | None) -> str | None:

        if not description:
            return description

        description = self._unescape_description_html(description=description)

        if not self._content_class_filter:
            return description

        parser = _HtmlClassExtractor(self._content_class_filter)
        try:
            parser.feed(description)
            parser.close()
        except Exception:  # pragma: no cover - defensive
            logger.debug(
                "Failed to extract content class %s from eBay description",
                self._content_class_filter,
                exc_info=True,
            )
            return description

        extracted = parser.get_content()
        if extracted:
            return extracted.strip()

        return description

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

            try:
                product = self._call_ebay_api(self.api.sell_inventory_get_inventory_item, sku=sku)
                if not isinstance(product, dict):
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
            except EbayAPIError as exc:
                if getattr(exc, "number", None) == 99404:
                    continue
                raise
            except EbayTemporarySystemError:
                logger.warning("Skipping SKU %s due to temporary eBay system error", sku)
                continue

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
        offer_data: dict[str, Any] | None = None,
        child_product_data: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Extract translation payloads and detected language."""

        if not isinstance(product_data, dict):
            return [], None

        inventory_item = product_data.get("product")
        if not isinstance(inventory_item, dict):
            inventory_item = product_data
            if not isinstance(inventory_item, dict):
                return [], None

        locale = product_data.get("locale")
        if (not isinstance(locale, str) or not locale) and isinstance(child_product_data, Mapping):
            locale = child_product_data.get("locale")

        if not isinstance(locale, str) or not locale:
            raise ValueError("Missing locale on eBay inventory item payload")

        remote_language = (
            EbayRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                remote_code__iexact=locale.replace('_','-'),
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
        if child_product_data is None and isinstance(offer_data, Mapping):
            for key in ("listing_description", "listingDescription"):
                value = offer_data.get(key)
                if isinstance(value, str) and value.strip():
                    listing_description = value.strip()
                    break

        if listing_description:
            description = listing_description

        description = self._filter_description_by_content_class(description)

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

        package_weight_size = product_data.get("package_weight_and_size")
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
            .select_related("local_instance")
            .prefetch_related("options__local_instance")
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
            "packageWeightAndSize__packageType": _normalize_single(package_weight_size.get("package_type")),
            "packageWeightAndSize__shippingIrregular": _normalize_single(package_weight_size.get("shipping_irregular")),
        }

        for code, value in internal_values.items():
            if value in (None, ""):
                continue

            internal_property = internal_properties.get(code)
            if not internal_property or not internal_property.local_instance:
                continue

            attribute_payload: dict[str, Any] = {
                "property": internal_property.local_instance,
                "value": value,
            }

            options_manager = getattr(internal_property, "options", None)
            if options_manager is not None:
                try:
                    normalized_value = str(value).strip().casefold()
                except Exception:
                    normalized_value = None

                if normalized_value:
                    for option in options_manager.all():
                        option_value = (option.value or "").strip()
                        if not option_value:
                            continue
                        if option_value.casefold() != normalized_value:
                            continue
                        local_instance_id = getattr(option, "local_instance_id", None)
                        if local_instance_id:
                            attribute_payload["value"] = local_instance_id
                            attribute_payload["value_is_id"] = True
                        break

            attributes.append(attribute_payload)

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

    def _extract_remote_id(self, payload: Any) -> str | None:
        """Return a stable remote identifier when present on the payload."""

        if not isinstance(payload, Mapping):
            return None

        candidate_keys = (
            "inventory_item_id",
            "inventoryItemId",
            "inventory_item_group_key",
            "inventoryItemGroupKey",
        )

        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        product_section = payload.get("product")
        if isinstance(product_section, Mapping):
            for key in candidate_keys:
                value = product_section.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None


    def get__product_data(
        self,
        *,
        product_data: dict[str, Any],
        offer_data: dict[str, Any],
        is_variation: bool,
        is_configurable: bool,
        product_instance: Any | None = None,
        child_product_data: dict[str, Any] | None = None,
        parent_skus: set[str] | None = None,
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
        is_active = True if is_configurable else bool(listing_status and str(listing_status).upper() == "ACTIVE")

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

        if isinstance(product_section, Mapping):
            ean_value = product_section.get("ean")
            if isinstance(ean_value, (list, tuple)):
                ean_value = ean_value[0] if ean_value else None
            if isinstance(ean_value, str):
                ean_value = ean_value.strip()
            if ean_value:
                structured["ean_code"] = ean_value

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
            offer_data=offer_data,
            child_product_data=child_product_data,
        )
        if translations:
            structured["translations"] = translations

        if is_configurable:
            configurator_values = self._parse_configurator_select_values(
                product_data=normalized_product,
            )
            if configurator_values:
                structured["configurator_select_values"] = configurator_values

        if is_variation and parent_skus:
            structured["configurable_parent_skus"] = [
                normalized
                for normalized in (
                    str(parent_sku).strip() for parent_sku in parent_skus if parent_sku is not None
                )
                if normalized
            ]

        structured["__marketplace_id"] = marketplace_id

        if is_configurable:
            variant_skus = product_data["variant_skus"]
            self._parent_child_sku_map[sku] = {
                str(value).strip()
                for value in variant_skus
                if value is not None and str(value).strip()
            }

        return structured, language, view


    def handle_attributes(self, *, import_instance: Any) -> None:
        """Synchronise local product properties with their eBay mirrors."""

        if not hasattr(import_instance, "properties"):
            return

        remote_product = getattr(import_instance, "remote_instance", None)
        if remote_product is None:
            return

        mirror_map = import_instance.data.get("__mirror_product_properties_map", {})
        if not isinstance(mirror_map, Mapping):
            mirror_map = {}

        product_properties = getattr(import_instance, "product_property_instances", [])

        for product_property in product_properties:
            local_property = getattr(product_property, "property", None)
            if local_property is None:
                continue

            mirror_data = mirror_map.get(local_property.id)
            if not mirror_data:
                continue

            remote_property = mirror_data.get("remote_property")
            remote_value = mirror_data.get("remote_value")
            remote_select_value = mirror_data.get("remote_select_value")
            remote_select_values = mirror_data.get("remote_select_values", [])

            if remote_property is None:
                continue

            remote_product_property, _ = EbayProductProperty.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=remote_product,
            )

            updated = False

            if remote_product_property.remote_property != remote_property:
                remote_product_property.remote_property = remote_property
                updated = True

            if remote_value is not None and not remote_product_property.remote_value:
                remote_product_property.remote_value = str(remote_value)
                updated = True

            if (
                hasattr(remote_product_property, "remote_select_value")
                and remote_product_property.remote_select_value != remote_select_value
            ):
                remote_product_property.remote_select_value = remote_select_value
                updated = True

            if updated:
                remote_product_property.save()

            if hasattr(remote_product_property, "remote_select_values"):
                existing_ids = set(
                    remote_product_property.remote_select_values.all().values_list("id", flat=True)
                )
                new_ids = {value.id for value in remote_select_values if value is not None}
                if existing_ids != new_ids:
                    remote_product_property.save()
                    remote_product_property.remote_select_values.set(remote_select_values)

        for mirror_data in mirror_map.values():
            if mirror_data.get("is_mapped"):
                continue

            remote_property = mirror_data.get("remote_property")
            remote_value = mirror_data.get("remote_value")
            remote_select_value = mirror_data.get("remote_select_value")
            remote_select_values = mirror_data.get("remote_select_values", [])

            if remote_property is None:
                continue

            local_instance: ProductProperty | None = None
            if remote_product.local_instance and remote_property.local_instance:
                local_instance = (
                    ProductProperty.objects.filter(
                        product=remote_product.local_instance,
                        property=remote_property.local_instance,
                    )
                    .select_related("property")
                    .first()
                )

            app, created = EbayProductProperty.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=remote_product,
                remote_property=remote_property,
                local_instance=local_instance,
            )

            changed = False

            if remote_value is not None and app.remote_value != str(remote_value):
                app.remote_value = str(remote_value)
                changed = True

            if (
                hasattr(app, "remote_select_value")
                and app.remote_select_value != remote_select_value
            ):
                app.remote_select_value = remote_select_value
                changed = True

            if changed or created:
                app.save()

            if hasattr(app, "remote_select_values"):
                existing_ids = set(app.remote_select_values.all().values_list("id", flat=True))
                new_ids = {value.id for value in remote_select_values if value is not None}
                if created or existing_ids != new_ids:
                    app.save()
                    app.remote_select_values.set(remote_select_values)

    def handle_variations(self, *, import_instance: Any, parent_skus) -> None:
        """Link variation mirrors to their parent and update the configurator when ready."""

        remote_variation = getattr(import_instance, "remote_instance", None)
        if remote_variation is None or not parent_skus:
            return

        variation_sku = None
        if hasattr(import_instance, "instance"):
            variation_sku = getattr(import_instance.instance, "sku", None)
        if not variation_sku and isinstance(getattr(import_instance, "data", {}), Mapping):
            variation_sku = import_instance.data.get("sku")
        if not variation_sku:
            variation_sku = getattr(remote_variation, "remote_sku", None)

        normalized_variation_sku = (
            str(variation_sku).strip() if variation_sku is not None else None
        )

        for parent_sku in parent_skus:
            normalized_parent_sku = (
                str(parent_sku).strip() if parent_sku is not None else ""
            )
            if not normalized_parent_sku:
                continue

            remote_parent = (
                EbayProduct.objects.filter(
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                    remote_sku=normalized_parent_sku,
                )
                .select_related("local_instance")
                .first()
            )
            if remote_parent is None:
                continue

            updated = False
            if not remote_variation.is_variation:
                remote_variation.is_variation = True
                updated = True

            if remote_variation.remote_parent_product_id != remote_parent.id:
                remote_variation.remote_parent_product = remote_parent
                updated = True

            if normalized_variation_sku and remote_variation.remote_sku != normalized_variation_sku:
                remote_variation.remote_sku = normalized_variation_sku
                updated = True

            if updated:
                remote_variation.save()

            child_skus = self._parent_child_sku_map.get(normalized_parent_sku)
            if not isinstance(child_skus, set):
                continue

            if normalized_variation_sku:
                child_skus.discard(normalized_variation_sku)

            is_last_child = not child_skus
            if not is_last_child:
                continue

            self._parent_child_sku_map.pop(normalized_parent_sku, None)

            parent_rule = import_instance.rule
            if parent_rule is None and remote_parent.local_instance is not None:
                parent_rule = remote_parent.local_instance.get_product_rule(
                    sales_channel=self.sales_channel,
                )

            if parent_rule is None or remote_parent.local_instance is None:
                continue

            variations_queryset = remote_parent.local_instance.get_configurable_variations(
                active_only=False
            )

            if hasattr(remote_parent, "configurator"):
                remote_parent.configurator.update_if_needed(
                    rule=parent_rule,
                    variations=variations_queryset,
                    send_sync_signal=False,
                )
            else:
                RemoteProductConfigurator.objects.create_from_remote_product(
                    remote_product=remote_parent,
                    rule=parent_rule,
                    variations=variations_queryset,
                )

    def handle_sales_channels_views(
        self,
        *,
        import_instance: Any,
        structured_data: dict[str, Any],
        view: EbaySalesChannelView | None = None,
        offer_data: dict[str, Any] | None = None,
        child_offer_data: dict[str, Any] | None = None,
    ) -> None:
        """Attach imported products to their eBay marketplace assignments."""

        def _extract_listing_details(*, payload: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
            if not isinstance(payload, Mapping):
                return None, None

            listing = payload.get("listing") if isinstance(payload, Mapping) else None
            if isinstance(listing, Mapping):
                listing_id = listing.get("listing_id") or listing.get("listingId")
                listing_status = listing.get("listing_status") or listing.get("listingStatus")
            else:
                listing_id = payload.get("listing_id") or payload.get("listingId")
                listing_status = payload.get("listing_status") or payload.get("listingStatus")

            normalized_id = str(listing_id).strip() if listing_id else None
            normalized_status = str(listing_status).strip() if listing_status else None
            return normalized_id or None, normalized_status or None

        remote_product = getattr(import_instance, "remote_instance", None)
        local_product = getattr(import_instance, "instance", None)

        if remote_product is None or local_product is None:
            return

        resolved_view = view

        if resolved_view is None and isinstance(structured_data, Mapping):
            marketplace_id = structured_data.get("__marketplace_id")
            if marketplace_id:
                resolved_view = (
                    EbaySalesChannelView.objects.filter(
                        sales_channel=self.sales_channel,
                        remote_id=str(marketplace_id).strip(),
                    )
                    .select_related()
                    .first()
                )

        if resolved_view is None:
            return

        assign, _ = SalesChannelViewAssign.objects.get_or_create(
            product=local_product,
            sales_channel_view=resolved_view,
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            defaults={"remote_product": remote_product},
        )

        updated_fields: list[str] = []

        if assign.remote_product_id != remote_product.id:
            assign.remote_product = remote_product
            updated_fields.append("remote_product")

        offer_payloads: tuple[Mapping[str, Any] | None, ...] = (
            offer_data if isinstance(offer_data, Mapping) else None,
            child_offer_data if isinstance(child_offer_data, Mapping) else None,
        )

        offer_id: str | None = None
        listing_id: str | None = None
        listing_status: str | None = None
        for payload in offer_payloads:
            if not isinstance(payload, Mapping):
                continue

            if offer_id is None:
                candidate = payload.get("offer_id")
                if candidate is not None:
                    normalized = str(candidate).strip()
                    if normalized:
                        offer_id = normalized

            lid, lstatus = _extract_listing_details(payload=payload)
            if listing_id is None and lid:
                listing_id = lid
            if listing_status is None and lstatus:
                listing_status = lstatus

        if offer_id and assign.remote_id != offer_id:
            assign.remote_id = offer_id
            updated_fields.append("remote_id")

        if updated_fields:
            assign.save(update_fields=updated_fields)

        offer_record = self._ensure_product_offer(
            remote_product=remote_product,
            sales_channel_view=resolved_view,
        )

        if offer_record is not None:
            offer_fields: list[str] = []
            if offer_id and offer_record.remote_id != offer_id:
                offer_record.remote_id = offer_id
                offer_fields.append("remote_id")
            if listing_id and offer_record.listing_id != listing_id:
                offer_record.listing_id = listing_id
                offer_fields.append("listing_id")
            if listing_status and offer_record.listing_status != listing_status:
                offer_record.listing_status = listing_status
                offer_fields.append("listing_status")

            if offer_fields:
                offer_record.save(update_fields=offer_fields)

        self._sync_product_category(
            product=local_product,
            view=resolved_view,
            offer_payloads=offer_payloads,
        )

    def _ensure_product_offer(
        self,
        *,
        remote_product: Any | None,
        sales_channel_view: EbaySalesChannelView | None,
    ) -> EbayProductOffer | None:
        if remote_product is None or sales_channel_view is None:
            return None

        offer, _ = EbayProductOffer.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            remote_product=remote_product,
            sales_channel_view=sales_channel_view,
        )

        return offer

    def _extract_offer_category_id(self, *offer_payloads: Mapping[str, Any] | None) -> str | None:
        """Return the normalized category_id from the first payload that declares it."""

        for payload in offer_payloads:
            if not isinstance(payload, Mapping):
                continue

            for key in ("category_id", "categoryId"):
                raw_value = payload.get(key)
                if raw_value is None:
                    continue

                normalized = str(raw_value).strip()
                if normalized:
                    return normalized

        return None

    def _sync_product_category(
        self,
        *,
        product: Any | None,
        view: EbaySalesChannelView | None,
        offer_payloads: tuple[Mapping[str, Any] | None, ...],
    ) -> None:
        """Ensure the local product has an EbayProductCategory entry for the offer."""

        if product is None or view is None:
            return

        category_id = self._extract_offer_category_id(*offer_payloads)
        if not category_id:
            return

        try:
            mapping, created = EbayProductCategory.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                sales_channel=self.sales_channel,
                view=view,
                defaults={"remote_id": category_id},
            )
        except ValidationError as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_CATEGORY_ASSIGNMENT,
                message="Invalid eBay category returned by offer",
                data={
                    "category_id": category_id,
                    "sku": getattr(product, "sku", None),
                },
                context={"product_id": getattr(product, "id", None), "view_id": view.id},
                exc=exc,
            )
            return

        if created or mapping.remote_id == category_id:
            return

        mapping.remote_id = category_id
        try:
            mapping.save(update_fields=["remote_id"])
        except ValidationError as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_CATEGORY_ASSIGNMENT,
                message="Invalid eBay category returned by offer",
                data={
                    "category_id": category_id,
                    "sku": getattr(product, "sku", None),
                },
                context={"product_id": getattr(product, "id", None), "view_id": view.id},
                exc=exc,
            )

    def update_remote_product(
        self,
        import_instance: Any,
        product_data: Any,
        view: EbaySalesChannelView | None,
        is_variation: bool,
    ) -> None:
        """Persist remote product metadata derived from the latest payload."""

        remote_product = getattr(import_instance, "remote_instance", None)
        if remote_product is None:
            return

        updates: list[str] = []

        sku_candidate = self._extract_sku(product_data)
        if not sku_candidate and isinstance(getattr(import_instance, "data", None), Mapping):
            sku_candidate = import_instance.data.get("sku")

        if sku_candidate:
            normalized_sku = str(sku_candidate).strip()
            if normalized_sku and remote_product.remote_sku != normalized_sku:
                remote_product.remote_sku = normalized_sku
                updates.append("remote_sku")

        remote_id = self._extract_remote_id(product_data)
        if remote_id and remote_product.remote_id != remote_id:
            remote_product.remote_id = remote_id
            updates.append("remote_id")

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100
            updates.append("syncing_current_percentage")

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation
            updates.append("is_variation")

        if not is_variation and remote_product.remote_parent_product_id is not None:
            remote_product.remote_parent_product = None
            updates.append("remote_parent_product")

        if updates:
            remote_product.save(update_fields=updates)

    def process_product_item(
        self,
        product_data: dict[str, Any],
        offer_data: dict[str, Any] | None = None,
        child_offer_data: dict[str, Any] | None = None,
        child_product_data: dict[str, Any] | None = None,
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
                normalized_parent_sku = parent_sku.strip() if isinstance(parent_sku, str) else str(parent_sku)

                if not normalized_parent_sku:
                    continue

                if normalized_parent_sku == sku or normalized_parent_sku in self._processed_parent_skus:
                    continue

                self._processed_parent_skus.add(normalized_parent_sku)

                try:
                    group_response = self.api.sell_inventory_get_inventory_item_group(
                        inventory_item_group_key=normalized_parent_sku,
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning(
                        "Failed to fetch inventory item group %s for SKU %s", normalized_parent_sku, sku, exc_info=exc
                    )
                    self._add_broken_record(
                        code=self.ERROR_PARENT_FETCH_FAILED,
                        message="Unable to fetch parent inventory item group",
                        data={"sku": sku, "parent_sku": normalized_parent_sku},
                        exc=exc,
                    )
                    continue

                if not isinstance(group_response, Mapping):
                    self._add_broken_record(
                        code=self.ERROR_PARENT_FETCH_FAILED,
                        message="Parent inventory group returned invalid data",
                        data={"sku": sku, "parent_sku": normalized_parent_sku},
                    )
                    continue

                parent_payload = dict(group_response)
                parent_payload.setdefault("sku", normalized_parent_sku)

                self.process_product_item(
                    parent_payload,
                    child_offer_data=offer_data,
                    child_product_data=product_data,
                )

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

        is_configurable = child_offer_data is not None and not is_variation

        rule = None
        if remote_product and remote_product.local_instance:
            existing_rule = remote_product.local_instance.get_product_rule(
                sales_channel=self.sales_channel,
            )
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
                child_product_data=child_product_data,
                parent_skus=parent_skus,
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
            update_current_rule=False,
        )

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

        if not is_configurable:
            self.handle_ean_code(import_instance=instance)
            self.handle_translations(import_instance=instance)
            self.handle_prices(import_instance=instance)
            self.handle_images(import_instance=instance)

        if parent_skus and is_variation:
            self.handle_variations(import_instance=instance, parent_skus=parent_skus)

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
            "data": data,
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
        offer_data: dict[str, Any],
        import_process,
        sales_channel,
        is_last: bool = False,
        updated_with: int | None = None,
    ) -> None:
        super().__init__(import_process=import_process, sales_channel=sales_channel)

        self.product_data = product_data
        self.offer_data = offer_data
        self.is_last = is_last
        self.updated_with = updated_with

    def run(self) -> None:
        """Execute the product import for the provided payload."""
        self.disable_inspector_signals()

        try:
            self.process_product_item(product_data=self.product_data, offer_data=self.offer_data)
        except Exception as exc:  # capture unexpected errors
            self._add_broken_record(
                code="UNKNOWN_ERROR",
                message="Unexpected error while processing product",
                data=self.product_data,
                exc=exc,
            )
        finally:
            self.refresh_inspector_status(run_inspection=False)

        if self.updated_with:
            increment_processed_records(self.import_process.id, delta=self.updated_with)
        if self.is_last:
            self.mark_success()
            self.process_completed()
