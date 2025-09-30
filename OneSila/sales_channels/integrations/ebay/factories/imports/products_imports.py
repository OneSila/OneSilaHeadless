"""Async product import scaffolding for the eBay integration."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any
from django.db.models import Q
from properties.models import Property

from currencies.models import Currency
from imports_exports.factories.imports import AsyncProductImportMixin, ImportMixin
from sales_channels.integrations.ebay.constants import EBAY_INTERNAL_PROPERTY_DEFAULTS
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import (
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
    EbayProductType,
    EbayRemoteLanguage
)
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

        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def process_completed(self):
        """Placeholder hook executed after the import finishes."""

        self.sales_channel.is_importing = False
        self.sales_channel.save(update_fields=["is_importing"])

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

    def get__product_data(self, product_data, offer_data, is_variation, is_configurable,  product_instance=None):
        # get sku product_data.get('sku')
        # get type is_configurable = CONFIGURABLE if not is SIMPLE
        # get the name (the product.title)
        # get view  offer_data marketplace_id
        # get language view ebay language
        # build initial structured data the actiive will be get by offer_data.listing.listing_status

        # if type == SIMPLE:
        #     prices, sales_pricelist_items = self._parse_prices(product_data, product_instance)
        #     if prices:
        #         structured["prices"] = prices
        #     if sales_pricelist_items:
        #         structured["sales_pricelist_items"] = sales_pricelist_items

        # attributes, mirror_map = self._parse_attributes(
        #     product_attrs, product_type_code, view
        # )
        # structured["properties"] = attributes
        # structured["__mirror_product_properties_map"] = mirror_map
        # structured["translations"] = self._parse_translations(name, language, product_data.get("attributes"))

        # if is_configurable:
        #     structured["configurator_select_values"] = self._parse_configurator_select_values(product_data)

        # structured["__marketplace_id"] = marketplace_id
        # return structured, language, view


        pass

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
