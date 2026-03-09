import pprint
import re
from decimal import Decimal
from django.utils import timezone
import logging
import traceback
from urllib.parse import urlparse
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.logging_helpers import AddLogTimeentry, timeit_and_log
from imports_exports.factories.imports import ImportMixin, AsyncProductImportMixin
from core.mixins import TemporaryDisableInspectorSignalsMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.mixins import UpdateOnlyInstanceNotFound
from products.models import Product, ProductTranslation
from products.product_types import SIMPLE, CONFIGURABLE
from properties.models import Property, ProductProperty
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.decorators import throttle_safe
from spapi import CatalogApi
from media.models import Image
from sales_channels.integrations.amazon.helpers import (
    infer_product_type,
    extract_description_and_bullets,
    get_is_product_variation, extract_amazon_attribute_value, is_amazon_internal_property,
)
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductType,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannelView,
    AmazonEanCode,
    AmazonProductProperty,
    AmazonPrice,
    AmazonProductContent,
    AmazonImageProductAssociation,
    AmazonDocumentType,
    AmazonDocumentThroughProduct,
    AmazonRemoteLanguage,
)

from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.models import SalesChannelViewAssign, SalesChannelIntegrationPricelist
from sales_prices.models import SalesPrice
from currencies.models import Currency
from core.helpers import ensure_serializable
from dateutil.parser import parse
from sales_channels.integrations.amazon.factories.sales_channels.issues import FetchRemoteIssuesFactory
import datetime
from imports_exports.helpers import append_amazon_broken_record, increment_processed_records
from sales_channels.integrations.amazon.models.imports import (
    AmazonImportRelationship,
    AmazonImportData,
)

logger = logging.getLogger(__name__)


class AmazonProductsImportProcessor(TemporaryDisableInspectorSignalsMixin, ImportMixin, GetAmazonAPIMixin, AddLogTimeentry):
    """Basic Amazon products import processor."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_BROKEN_IMPORT_PROCESS = "BROKEN_IMPORT_PROCESS"
    ERROR_MISSING_DATA = "MISSING_DATA"
    ERROR_NO_MAPPED_PRODUCT_TYPE = "NO_MAPPED_PRODUCT_TYPE"
    ERROR_PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"
    ERROR_UPDATE_ONLY_NOT_FOUND = "UPDATE_ONLY_NOT_FOUND"
    ERROR_NAME_TOO_LONG = "NAME_TOO_LONG"
    ERROR_INVALID_VARIATION_THEME = "INVALID_VARIATION_THEME"

    def _add_broken_record(self, *, code, message, data=None, context=None, exc=None):
        record = {
            "data": ensure_serializable(data) if data else {},
            "context": context or {},
            "code": code,
            "message": message,
        }
        if exc is not None:
            record["error"] = str(exc)
            record["traceback"] = traceback.format_exc()

        self.broken_records.append(record)

        append_amazon_broken_record(self.import_process.id, record)

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)
        self.sales_channel = sales_channel
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self.api = self.get_api()
        self.broken_records: list[dict] = []
        self._mapped_document_types_by_remote_id_cache = None
        self._language_map_by_view_id = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def prepare_import_process(self):
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def process_completed(self):
        self.sales_channel.is_importing = False
        self.sales_channel.save(update_fields=["is_importing"])

        if self.broken_records:
            self.import_process.broken_records = self.broken_records
            self.import_process.save(update_fields=["broken_records"])

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------
    @timeit_and_log(logger, "AmazonProductsImportProcessor.get_total_instances")
    def get_total_instances(self):
        return self.get_total_number_of_products()

    @timeit_and_log(logger, "AmazonProductsImportProcessor.get_products_data")
    def get_products_data(self):
        # Delegate to the mixin helper which yields ListingItem objects
        yield from self.get_all_products(sort_order="DESC")

    # ------------------------------------------------------------------
    # Structuring
    # ------------------------------------------------------------------
    def _get_summary(self, product):
        summaries = product.get("summaries") or []
        return summaries[0] if summaries else {}

    def _parse_prices(self, product, local_product=None):
        prices = []
        sales_pricelist_items = []
        processed = set()

        for offer in product.get("offers", []):

            if offer.get("offer_type") != "B2C":
                continue

            price_info = offer.get("price") or {}
            amount = price_info.get("amount")
            currency_code = price_info.get("currency_code")

            if amount is None or not currency_code or currency_code in processed:
                continue

            processed.add(currency_code)

            try:
                currency = Currency.objects.get(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    iso_code=currency_code,
                )
            except Currency.DoesNotExist as exc:
                raise ValueError(
                    f"Currency with ISO code {currency_code} does not exist locally"
                ) from exc

            scip = SalesChannelIntegrationPricelist.objects.filter(
                sales_channel=self.sales_channel,
                price_list__currency=currency,
            ).select_related("price_list").first()

            price_decimal = Decimal(amount)

            if scip:
                sales_pricelist_items.append({
                    "salespricelist": scip.price_list,
                    "disable_auto_update": True,
                    "price_auto": price_decimal,
                })
            else:
                sales_pricelist_items.append({
                    "salespricelist_data": {
                        "name": f"Amazon {self.sales_channel.hostname} {currency_code}",
                        "currency_object": currency,
                    },
                    "disable_auto_update": True,
                    "price_auto": price_decimal,
                })

            has_sales_price = (
                local_product
                and SalesPrice.objects.filter(
                    product=local_product,
                    currency__iso_code=currency_code,
                ).exists()
            )

            if not has_sales_price:
                prices.append({
                    "price": price_decimal,
                    "currency": currency_code,
                })

        return prices, sales_pricelist_items

    def _parse_translations(self, name, language, attributes_dict):
        description, bullets = extract_description_and_bullets(attributes_dict)

        return [
            {
                "name": name,
                "description": description,
                "bullet_points": bullets,
                "language": language,
            }
        ]

    def _parse_images(self, product):
        attrs = product.get("attributes") or {}
        images = []
        index = 0

        for value in attrs.get("main_product_image_locator", []):
            url = value.get("media_location")
            if not url:
                continue
            images.append({
                "image_url": url,
                "sort_order": index,
                "is_main_image": index == 0,
            })
            index += 1

        for i in range(1, 9):
            key = f"other_product_image_locator_{i}"
            for value in attrs.get(key, []):
                url = value.get("media_location")
                if not url:
                    continue
                images.append({
                    "image_url": url,
                    "sort_order": index,
                    "is_main_image": index == 0,
                })
                index += 1

        for value in attrs.get("swatch_product_image_locator", []):
            url = value.get("media_location")
            if not url:
                continue
            images.append({
                "image_url": url,
                "sort_order": index,
                "is_main_image": False,
                "type": Image.COLOR_SHOT,
            })
            index += 1

        if index == 0:
            summaries = product.get("summaries") or []
            if summaries:
                main_image = summaries[0].get("main_image") or {}
                link = main_image.get("link")
                if link:
                    images.append({
                        "image_url": link,
                        "sort_order": index,
                        "is_main_image": index == 0,
                    })

        return images

    @staticmethod
    def _normalise_document_entries(*, values):
        if values is None:
            return []

        if isinstance(values, (list, tuple, set)):
            iterable = list(values)
        else:
            iterable = [values]

        entries = []
        for value in iterable:
            if value is None:
                continue
            if isinstance(value, dict):
                entries.append(value)
            else:
                entries.append({"value": value})

        return entries

    @staticmethod
    def _extract_document_url(*, value):
        candidate = value
        if isinstance(value, dict):
            for key in ("source_location", "media_location", "value", "document_url", "url", "link"):
                maybe_url = value.get(key)
                if maybe_url not in (None, ""):
                    candidate = maybe_url
                    break
            else:
                return None

        normalized = str(candidate or "").strip()
        if not normalized:
            return None

        parsed = urlparse(normalized)
        if parsed.scheme.lower() != "https":
            return None
        if not parsed.netloc:
            return None

        return normalized

    def _resolve_local_document_language(self, *, view, remote_language_code):
        view_id = getattr(view, "id", None)
        if view_id not in self._language_map_by_view_id:
            language_map = (
                AmazonRemoteLanguage.objects.filter(
                    sales_channel=self.sales_channel,
                    sales_channel_view=view,
                )
                .exclude(local_instance__isnull=True)
                .exclude(local_instance="")
                .values_list("remote_code", "local_instance")
            )

            normalized_map = {}
            for remote_value, local_value in language_map:
                key = str(remote_value or "").strip().lower()
                if key and key not in normalized_map:
                    normalized_map[key] = local_value
            self._language_map_by_view_id[view_id] = normalized_map

        normalized_map = self._language_map_by_view_id.get(view_id, {})
        remote_code = str(remote_language_code or "").strip()
        if remote_code:
            normalized_remote = remote_code.replace("-", "_").lower()
            if normalized_remote in normalized_map:
                return normalized_map[normalized_remote]

            language_root = normalized_remote.split("_")[0]
            for remote_value, local_value in normalized_map.items():
                if remote_value.split("_")[0] == language_root:
                    return local_value

            if language_root:
                return language_root

        return (
            getattr(view, "language_tag_local", None)
            or getattr(self.sales_channel.multi_tenant_company, "language", None)
            or None
        )

    def _get_mapped_document_types_by_remote_id(self):
        if self._mapped_document_types_by_remote_id_cache is not None:
            return self._mapped_document_types_by_remote_id_cache

        mapped_by_remote_id = {}
        queryset = (
            AmazonDocumentType.objects.filter(sales_channel=self.sales_channel)
            .exclude(local_instance__isnull=True)
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .select_related("local_instance")
            .order_by("id")
        )

        for remote_document_type in queryset:
            remote_id = str(remote_document_type.remote_id or "").strip()
            if not remote_id:
                continue
            if remote_id in mapped_by_remote_id:
                continue
            mapped_by_remote_id[remote_id] = remote_document_type.local_instance

        self._mapped_document_types_by_remote_id_cache = mapped_by_remote_id
        return self._mapped_document_types_by_remote_id_cache

    def _parse_documents(self, *, product_data, view, catalog_attributes=None):
        mapped_by_remote_id = self._get_mapped_document_types_by_remote_id()
        if not mapped_by_remote_id:
            return [], {}

        attributes_sources = []
        product_attributes = product_data.get("attributes") or {}
        if isinstance(product_attributes, dict):
            attributes_sources.append(product_attributes)
        if isinstance(catalog_attributes, dict) and catalog_attributes:
            attributes_sources.append(catalog_attributes)

        if not attributes_sources:
            return [], {}

        documents = []
        document_remote_id_map = {}
        seen_document_keys = set()

        def _append_document(
            *,
            remote_mapping_id,
            remote_property_code,
            raw_document,
            remote_language_code=None,
        ):
            local_document_type = mapped_by_remote_id.get(remote_mapping_id)
            if local_document_type is None:
                return

            document_url = self._extract_document_url(value=raw_document)
            if not document_url:
                return

            dedupe_key = (
                document_url,
                local_document_type.id,
                str(remote_property_code or "").strip(),
            )
            if dedupe_key in seen_document_keys:
                return

            local_language = self._resolve_local_document_language(
                view=view,
                remote_language_code=remote_language_code,
            )

            payload = {
                "document_url": document_url,
                "document_type": local_document_type,
                "sort_order": len(documents),
            }
            if local_language:
                payload["document_language"] = local_language

            documents.append(payload)
            document_remote_id_map[str(len(documents) - 1)] = str(remote_property_code or "").strip()
            seen_document_keys.add(dedupe_key)

        for attrs in attributes_sources:
            if not isinstance(attrs, dict):
                continue

            for entry in self._normalise_document_entries(values=attrs.get("compliance_media")):
                content_type = str(entry.get("content_type") or "").strip().lower()
                if not content_type:
                    continue
                _append_document(
                    remote_mapping_id=f"compliance_media__{content_type}",
                    remote_property_code="compliance_media",
                    raw_document=entry.get("source_location") or entry,
                    remote_language_code=entry.get("content_language"),
                )

            for entry in self._normalise_document_entries(values=attrs.get("safety_data_sheet_url")):
                _append_document(
                    remote_mapping_id="safety_data_sheet_url",
                    remote_property_code="safety_data_sheet_url",
                    raw_document=entry,
                    remote_language_code=entry.get("language_tag") if isinstance(entry, dict) else None,
                )

            for ps_index in range(1, 7):
                property_code = f"image_locator_ps{ps_index:02d}"
                for entry in self._normalise_document_entries(values=attrs.get(property_code)):
                    _append_document(
                        remote_mapping_id="image_locator_ps",
                        remote_property_code=property_code,
                        raw_document=entry,
                        remote_language_code=entry.get("language_tag") if isinstance(entry, dict) else None,
                    )

            for code, raw_values in attrs.items():
                normalized_code = str(code or "").strip().lower()
                if not re.match(r"^image_locator_.*pf$", normalized_code):
                    continue

                for entry in self._normalise_document_entries(values=raw_values):
                    _append_document(
                        remote_mapping_id="image_locator_pf",
                        remote_property_code=str(code or "").strip(),
                        raw_document=entry,
                        remote_language_code=entry.get("language_tag") if isinstance(entry, dict) else None,
                    )

        return documents, document_remote_id_map

    @timeit_and_log(logger, "AmazonProductsImportProcessor._parse_attributes")
    def _parse_attributes(self, attributes, product_type, marketplace):
        attrs = []
        mirror_map = {}
        product_attrs = attributes or {}

        for code, values in product_attrs.items():

            if is_amazon_internal_property(code=code):
                continue

            definition = AmazonPublicDefinition.objects.filter(
                code=code,
                api_region_code=marketplace.api_region_code,
                product_type_code=product_type).first()

            if definition is None:
                continue

            if definition.export_definition:
                for value in definition.export_definition:
                    real_code = value.get("code")
                    remote_property = AmazonProperty.objects.filter(sales_channel=self.sales_channel, code=real_code).first()

                    if not remote_property or not remote_property.local_instance:
                        continue

                    value = extract_amazon_attribute_value({code: values[0]}, real_code)
                    if value is None:
                        logger.warning(
                            "Could not extract value for attribute '%s' (real code '%s') with entry %s",
                            code,
                            real_code,
                            values[0],
                        )
                        continue

                    if remote_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
                        max_len = AmazonPropertySelectValue._meta.get_field("remote_value").max_length
                        val_str = str(value) if value is not None else ""
                        if not val_str or len(val_str) > max_len:
                            continue

                        select_value = AmazonPropertySelectValue.objects.filter(
                            amazon_property=remote_property,
                            remote_value=value,
                            marketplace=marketplace
                        ).first()

                        if select_value is None and remote_property.allows_unmapped_values:
                            new_remote_select_value, _ = AmazonPropertySelectValue.objects.get_or_create(
                                multi_tenant_company=self.sales_channel.multi_tenant_company,
                                sales_channel=self.sales_channel,
                                marketplace=marketplace,
                                amazon_property=remote_property,
                                remote_value=value,
                            )

                            new_remote_select_value.remote_name = value
                            new_remote_select_value.save()
                            select_value = new_remote_select_value

                        mapped = bool(select_value and select_value.local_instance)
                        if mapped:
                            attrs.append({
                                "property": remote_property.local_instance,
                                "value": select_value.local_instance.id,
                                "value_is_id": True,
                            })

                        mirror_map[remote_property.local_instance.id] = {
                            "remote_property": remote_property,
                            "remote_value": value,
                            "is_mapped": mapped,
                            "remote_select_value": select_value,
                            "remote_select_values": [select_value] if select_value else [],
                        }

                        continue

                    elif remote_property.type == Property.TYPES.DATE:

                        try:
                            parsed = parse(value).date()
                            value = parsed.strftime('%Y-%m-%d')
                        except Exception:
                            pass

                    elif remote_property.type == Property.TYPES.DATETIME:
                        try:
                            parsed = parse(value)
                            value = parsed.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            pass

                    attrs.append({"property": remote_property.local_instance, "value": value})
                    mirror_map[remote_property.local_instance.id] = {
                        "remote_property": remote_property,
                        "remote_value": value,
                        "is_mapped": True,
                        "remote_select_value": None,
                        "remote_select_values": [],
                    }

        return attrs, mirror_map

    def get_catalog_api_client(self):
        return CatalogApi(self._get_client())

    @throttle_safe(max_retries=5, base_delay=1)
    def _fetch_catalog_attributes(self, asin, view):
        """Fetch additional catalog attributes for a product."""
        if not asin or not view:
            return {}

        catalog_api = self.get_catalog_api_client()
        try:
            response = catalog_api.get_catalog_item(
                asin,
                [view.remote_id],
                included_data=["attributes"],
            )
        except Exception:
            return {}

        if isinstance(response, dict):
            return response.get("attributes", {})

        if hasattr(response, "attributes"):
            return response.attributes or {}

        if hasattr(response, "payload"):
            payload = getattr(response, "payload", None)
            if isinstance(payload, dict):
                return payload.get("attributes", {})
            return getattr(payload, "attributes", {}) or {}

        return {}

    @timeit_and_log(logger)
    def _parse_configurator_select_values(self, product):
        configurator_values = []
        amazon_theme = None
        relationships = product.get("relationships") or []
        for relation in relationships:
            for rel in relation.get("relationships", []):
                vt = rel.get("variation_theme")
                if not vt:
                    continue
                attrs = vt.get("attributes") or []
                amazon_theme = vt.get("theme")
                for code in attrs:
                    remote_property = AmazonProperty.objects.filter(
                        sales_channel=self.sales_channel,
                        code=code,
                    ).first()
                    if remote_property and remote_property.local_instance:
                        configurator_values.append({"property": remote_property.local_instance})
                if attrs:
                    break
            if configurator_values:
                break
        return configurator_values, amazon_theme

    def get_product_rule(self, product_data):
        summary = self._get_summary(product_data)
        product_type_code = summary.get("product_type")
        rule = None

        if product_type_code:
            rule = AmazonProductType.objects.filter(
                sales_channel=self.sales_channel,
                product_type_code=product_type_code,
            ).order_by("id").first()

            if rule:
                rule = rule.local_instance

        return rule

    def _get_language_for_marketplace(self, view):

        if not view:
            return None

        remote_lang = view.remote_languages.first()
        return remote_lang.local_instance if remote_lang else None

    @timeit_and_log(logger, "AmazonProductsImportProcessor.get__product_data")
    def get__product_data(self, product_data, is_variation, product_instance=None):
        summary = self._get_summary(product_data)
        asin = summary.get("asin")
        sku = product_data.get("sku")
        type = infer_product_type(product_data, is_variation)
        marketplace_id = summary.get("marketplace_id")
        product_type_code = summary.get("product_type")
        product_attrs = product_data.get("attributes") or {}

        name_entry = product_attrs.get("item_name")
        if isinstance(name_entry, list):
            name_entry = name_entry[0] if name_entry else None
        if isinstance(name_entry, dict):
            name = name_entry.get("value") or name_entry.get("name")
        else:
            name = None

        if not name:
            name = summary.get("item_name")

        # it seems that sometimes the name can be None coming from Amazon. IN that case we fallback to sku
        if name is None:
            name = sku

        max_name_len = ProductTranslation._meta.get_field("name").max_length
        if name and len(name) > max_name_len:
            self._add_broken_record(
                code=self.ERROR_NAME_TOO_LONG,
                message="Product name exceeds maximum length",
                data={"sku": sku, "name": name[:max_name_len]},
            )
            name = name[:max_name_len]

        if marketplace_id is None:
            raise ValueError("Missing marketplace_id in Amazon summary data.")

        view = AmazonSalesChannelView.objects.get(
            sales_channel=self.sales_channel,
            remote_id=marketplace_id,
        )
        language = self._get_language_for_marketplace(view)

        structured = {
            "name": name,
            "sku": sku,
            "type": type
        }

        structured["images"] = self._parse_images(product_data)

        if type == SIMPLE:
            prices, sales_pricelist_items = self._parse_prices(product_data, product_instance)
            if prices:
                structured["prices"] = prices
            if sales_pricelist_items:
                structured["sales_pricelist_items"] = sales_pricelist_items

        attributes, mirror_map = self._parse_attributes(
            product_attrs, product_type_code, view
        )

        catalog_attrs = self._fetch_catalog_attributes(asin, view)
        if catalog_attrs:
            extra_attrs, extra_map = self._parse_attributes(
                catalog_attrs,
                product_type_code,
                view,
            )
            existing_ids = {
                getattr(a.get("property"), "id", None) for a in attributes
            }
            for attr in extra_attrs:
                prop_id = getattr(attr.get("property"), "id", None)
                if prop_id not in existing_ids:
                    attributes.append(attr)
                    existing_ids.add(prop_id)
            for k, v in extra_map.items():
                if k not in mirror_map:
                    mirror_map[k] = v

        documents, document_remote_id_map = self._parse_documents(
            product_data=product_data,
            view=view,
            catalog_attributes=catalog_attrs,
        )
        if documents:
            structured["documents"] = documents
            structured["__document_index_to_remote_id"] = document_remote_id_map

        if attributes:
            structured["properties"] = attributes
            structured["__mirror_product_properties_map"] = mirror_map

        structured["translations"] = self._parse_translations(name, language, product_data.get("attributes"))
        configurator_values, amazon_theme = self._parse_configurator_select_values(product_data)

        if configurator_values:
            structured["configurator_select_values"] = configurator_values

        if amazon_theme:
            structured["__amazon_theme"] = amazon_theme

        gtin_entry = product_attrs.get(
            "supplier_declared_has_product_identifier_exemption"
        )
        if isinstance(gtin_entry, list):
            gtin_entry = gtin_entry[0] if gtin_entry else None
        if isinstance(gtin_entry, dict):
            gtin_exemption = gtin_entry.get("value")
        else:
            gtin_exemption = None
        if gtin_exemption is not None:
            structured["__gtin_exemption"] = bool(gtin_exemption)

        browse_nodes = product_attrs.get("recommended_browse_nodes")
        if not browse_nodes:
            browse_nodes = product_data.get("recommended_browse_nodes")

        if browse_nodes:
            first_node = browse_nodes[0] if isinstance(browse_nodes, list) else browse_nodes
            browse_node_id = None
            if isinstance(first_node, dict):
                browse_node_id = first_node.get("value") or first_node.get("id")
            elif isinstance(first_node, (str, int)):
                browse_node_id = first_node

            if browse_node_id:
                structured["__recommended_browse_node_id"] = browse_node_id

        structured["__asin"] = asin
        structured["__marketplace_id"] = marketplace_id

        return structured, language, view

    def update_product_import_instance(self, instance: ImportProductInstance):
        instance.prepare_mirror_model_class(
            mirror_model_class=AmazonProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
        )

    def update_remote_product(self, import_instance: ImportProductInstance, product, view, is_variation: bool):
        remote_product = import_instance.remote_instance
        asin = import_instance.data.get("__asin")

        sku = product.get("sku")
        if sku and not remote_product.remote_sku:
            remote_product.remote_sku = sku

        if asin and view:
            from sales_channels.integrations.amazon.models import AmazonExternalProductId

            AmazonExternalProductId.objects.update_or_create(
                product=remote_product.local_instance,
                view=view,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={
                    "value": asin,
                    "type": AmazonExternalProductId.TYPE_ASIN,
                    "created_asin": asin,
                },
            )

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation

        if view.remote_id not in (remote_product.created_marketplaces or []):
            remote_product.created_marketplaces.append(view.remote_id)

        remote_product.save()

    def handle_ean_code(self, import_instance: ImportProductInstance):
        ean_qs = AmazonEanCode.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )
        amazon_ean_code = ean_qs.first()
        if amazon_ean_code is None:
            amazon_ean_code = AmazonEanCode.objects.create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
            )

        if hasattr(import_instance, "ean_code") and import_instance.ean_code:
            if amazon_ean_code.ean_code != import_instance.ean_code:
                amazon_ean_code.ean_code = import_instance.ean_code
                amazon_ean_code.save()

    @timeit_and_log(logger)
    def handle_attributes(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "properties"):
            product_properties = import_instance.product_property_instances
            remote_product = import_instance.remote_instance
            mirror_map = import_instance.data.get("__mirror_product_properties_map", {})

            for product_property in product_properties:
                mirror_data = mirror_map.get(product_property.property.id)

                if not mirror_data:
                    continue

                remote_property = mirror_data["remote_property"]
                remote_value = mirror_data["remote_value"]
                remote_select_value = mirror_data.get("remote_select_value")
                remote_select_values = mirror_data.get("remote_select_values", [])

                remote_product_property, _ = AmazonProductProperty.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=product_property,
                    remote_product=remote_product,
                )

                updated = False

                if remote_product_property.remote_property != remote_property:
                    remote_product_property.remote_property = remote_property
                    updated = True

                if not remote_product_property.remote_value:
                    remote_product_property.remote_value = remote_value
                    updated = True

                if remote_product_property.remote_select_value != remote_select_value:
                    remote_product_property.remote_select_value = remote_select_value
                    updated = True

                existing_ids = set(remote_product_property.remote_select_values.all().values_list("id", flat=True))
                new_ids = {v.id for v in remote_select_values}
                if existing_ids != new_ids:
                    remote_product_property.save()
                    remote_product_property.remote_select_values.set(remote_select_values)

                if updated:
                    remote_product_property.save()

            # Handle unmapped remote properties (those with mapped=False)
            for local_id, mirror_data in mirror_map.items():

                if mirror_data["is_mapped"]:
                    continue  # already handled in the mapped loop

                remote_property = mirror_data["remote_property"]
                remote_select_value = mirror_data.get("remote_select_value")
                remote_select_values = mirror_data.get("remote_select_values", [])

                local_instance = None
                if remote_product.local_instance and remote_property.local_instance:
                    local_instance = ProductProperty.objects.filter(
                        product=remote_product.local_instance,
                        property=remote_property.local_instance,
                    ).first()

                app, created = AmazonProductProperty.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    remote_product=remote_product,
                    remote_property=remote_property,
                    local_instance=local_instance,
                )

                if created or app.remote_select_value != remote_select_value:
                    app.remote_select_value = remote_select_value
                    app.save()

                if created:
                    app.remote_select_values.set(remote_select_values)
                else:
                    existing_ids = set(app.remote_select_values.all().values_list("id", flat=True))
                    new_ids = {v.id for v in remote_select_values}
                    if existing_ids != new_ids:
                        app.save()
                        app.remote_select_values.set(remote_select_values)

    @timeit_and_log(logger)
    def handle_translations(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "translations"):
            AmazonProductContent.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
            )

    @timeit_and_log(logger)
    def handle_prices(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "prices"):
            remote_product = import_instance.remote_instance
            amazon_price, _ = AmazonPrice.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=remote_product,
            )

            price_data = {}
            for price_entry in import_instance.prices:
                currency = price_entry.get("currency")
                price = price_entry.get("price")
                rrp = price_entry.get("rrp")

                data = {}
                if rrp is not None:
                    data["price"] = float(rrp)
                if price is not None:
                    data["discount_price"] = float(price)

                if data:
                    price_data[currency] = data

            if price_data:
                amazon_price.price_data = price_data
                amazon_price.save()

    @timeit_and_log(logger)
    def handle_images(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "images"):
            for index, image_ass in enumerate(import_instance.images_associations_instances):
                imported_url = None
                if index < len(import_instance.images):
                    imported_url = import_instance.images[index].get("image_url")

                instance, _ = AmazonImageProductAssociation.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=image_ass,
                    remote_product=import_instance.remote_instance,
                )

                if imported_url and instance.imported_url != imported_url:
                    instance.imported_url = imported_url
                    instance.save(update_fields=["imported_url"])

    @timeit_and_log(logger)
    def handle_documents(self, *, import_instance: ImportProductInstance):
        if not hasattr(import_instance, "documents"):
            return

        remote_id_map = import_instance.data.get("__document_index_to_remote_id", {})

        for index, document_association in enumerate(import_instance.documents_associations_instances):
            remote_property_code = str(remote_id_map.get(str(index)) or "").strip()
            document_payload = import_instance.documents[index] if index < len(import_instance.documents) else {}
            remote_url = str(document_payload.get("document_url") or "").strip() if isinstance(document_payload, dict) else ""

            remote_association = (
                AmazonDocumentThroughProduct.objects.filter(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=document_association,
                    remote_product=import_instance.remote_instance,
                )
                .order_by("id")
                .first()
            )
            if remote_association is None:
                remote_association = AmazonDocumentThroughProduct.objects.create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=document_association,
                    remote_product=import_instance.remote_instance,
                    remote_document=None,
                    require_document=False,
                    remote_id=remote_property_code or None,
                    remote_url=remote_url or None,
                )
                continue

            update_fields = []
            if remote_association.require_document:
                remote_association.require_document = False
                update_fields.append("require_document")
            if remote_association.remote_document_id is not None:
                remote_association.remote_document = None
                update_fields.append("remote_document")
            if remote_property_code and remote_association.remote_id != remote_property_code:
                remote_association.remote_id = remote_property_code
                update_fields.append("remote_id")
            if remote_url and remote_association.remote_url != remote_url:
                remote_association.remote_url = remote_url
                update_fields.append("remote_url")

            if update_fields:
                remote_association.save(update_fields=update_fields)

    @timeit_and_log(logger)
    def handle_variations(self, import_instance: ImportProductInstance, view):
        from sales_channels.models.products import RemoteProductConfigurator
        from sales_channels.integrations.amazon.models import (
            AmazonVariationTheme,
            AmazonProductType,
        )

        theme = import_instance.data.get("__amazon_theme")

        remote_product = import_instance.remote_instance
        if hasattr(remote_product, "configurator"):
            configurator = remote_product.configurator
            configurator.update_if_needed(
                rule=import_instance.rule,
                send_sync_signal=False,
            )
        else:
            RemoteProductConfigurator.objects.create_from_remote_product(
                remote_product=remote_product,
                rule=import_instance.rule,
                variations=None,
            )

        if theme and view:
            try:
                AmazonVariationTheme.objects.update_or_create(
                    product=import_instance.instance,
                    view=view,
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    defaults={"theme": theme},
                )
            except ValidationError as e:
                product_type = None
                allowed = []
                try:
                    rule = import_instance.instance.get_product_rule(
                        sales_channel=view.sales_channel,
                    )
                    remote_rule = AmazonProductType.objects.get(
                        local_instance=rule,
                        sales_channel=view.sales_channel,
                    )
                    product_type = remote_rule.product_type_code
                    allowed = remote_rule.variation_themes or []
                except Exception:
                    pass
                self._add_broken_record(
                    code=self.ERROR_INVALID_VARIATION_THEME,
                    message="Invalid variation theme for product type",
                    data={"theme": theme},
                    context={
                        "sku": import_instance.data.get("sku"),
                        "asin": import_instance.data.get("__asin"),
                        "product_type": product_type,
                        "allowed_variation_themes": allowed,
                    },
                    exc=e,
                )

    @timeit_and_log(logger)
    def handle_gtin_exemption(self, import_instance: ImportProductInstance, view):
        from sales_channels.integrations.amazon.models import AmazonGtinExemption

        if not view:
            return

        exemption = import_instance.data.get("__gtin_exemption")
        if exemption is None:
            AmazonGtinExemption.objects.filter(
                product=import_instance.instance,
                view=view,
                multi_tenant_company=self.import_process.multi_tenant_company,
            ).delete()
            return

        AmazonGtinExemption.objects.update_or_create(
            product=import_instance.instance,
            view=view,
            multi_tenant_company=self.import_process.multi_tenant_company,
            defaults={"value": bool(exemption)},
        )

    @timeit_and_log(logger)
    def handle_product_browse_node(self, import_instance: ImportProductInstance, view):
        from sales_channels.integrations.amazon.models import AmazonProductBrowseNode

        if not view:
            return

        node_id = import_instance.data.get("__recommended_browse_node_id")
        if node_id:
            AmazonProductBrowseNode.objects.update_or_create(
                product=import_instance.instance,
                sales_channel=self.sales_channel,
                view=view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                defaults={"remote_id": node_id},
            )
        else:
            AmazonProductBrowseNode.objects.filter(
                product=import_instance.instance,
                sales_channel=self.sales_channel,
                view=view,
                multi_tenant_company=self.import_process.multi_tenant_company,
            ).delete()

    def handle_sales_channels_views(self, import_instance: ImportProductInstance, structured_data, view):
        if not view:
            return

        try:
            assign, _ = SalesChannelViewAssign.objects.get_or_create(
                product=import_instance.instance,
                sales_channel_view=view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                remote_product=import_instance.remote_instance,
                sales_channel=self.sales_channel,
            )
        except IntegrityError as e:
            raise IntegrityError(
                f"Failed to create SalesChannelViewAssign due to unique constraint violation.\n"
                f"product_id={import_instance.instance.id}, "
                f"sales_channel_view_id={view.id}, "
                f"multi_tenant_company_id={self.import_process.multi_tenant_company.id}, "
                f"remote_product_id={getattr(import_instance.remote_instance, 'id', 'N/A')}, "
                f"sales_channel_id={self.sales_channel.id}"
            ) from e

    @timeit_and_log(logger, "AmazonProductsImportProcessor.process_product_item")
    def process_product_item(self, product):

        # Kickstarting the AddLogTimeentry class settings.
        self._set_logger(logger)
        self._set_start_time(f"process_product_item for sku: {product.get('sku')} - before settings prodduct Instance.")

        product_instance = None
        qs = AmazonProduct.objects.filter(
            remote_sku=product.get("sku"),
            sales_channel=self.sales_channel,
            multi_tenant_company=self.import_process.multi_tenant_company
        )
        remote_product = qs.first()
        is_variation, parent_skus = get_is_product_variation(product)
        if remote_product:
            is_variation = remote_product.is_variation
            product_instance = remote_product.local_instance

        self._set_start_time(f"process_product_item for sku: {product.get('sku')} - before getting summary")

        summary = self._get_summary(product)

        if not product.get("summaries"):
            self._add_broken_record(
                code=self.ERROR_MISSING_DATA,
                message="Missing summary data from Amazon API",
                data=product,
                context={"sku": product.get("sku")},
            )
            return

        rule = None
        # Ensure we keep the rule from the default marketplace if the product
        # already exists. This prevents overriding the initial rule when
        # importing the product from additional marketplaces with a different
        # product type.
        if remote_product and remote_product.local_instance:
            existing_rule = remote_product.local_instance.get_product_rule(
                sales_channel=self.sales_channel,
            )
            if existing_rule:
                rule = existing_rule

        if rule is None:
            rule = self.get_product_rule(product)

        structured, language, view = self.get__product_data(product, is_variation, product_instance)

        # if on the main marketplaces was configurable because the other doesn't have relationships
        # will return SIMPLE as default which is wrong
        if remote_product and remote_product.local_instance:
            structured['type'] = remote_product.local_instance.type

        missing_data = (
            not product.get("attributes")
            or not product.get("summaries")
            or not summary.get("product_type")
        )

        self._add_log_entry(f"getting structured data - {product.get('sku')} - before checking remote products")
        if remote_product and not missing_data:
            try:
                existing_code = remote_product.remote_type
            except Exception:
                existing_code = None

            incoming_code = summary.get("product_type")
            if existing_code and incoming_code and existing_code != incoming_code:
                # if the current product type code is different from the original one (main store)
                # we will add it as a broken record. It will continue the flow and probably override it
                # but at least we know something was broken here
                self._add_broken_record(
                    code=self.ERROR_PRODUCT_TYPE_MISMATCH,
                    message="Remote product type mismatch",
                    data=structured,
                    context={"sku": structured.get("sku"), "asin": structured.get("__asin")},
                )

        self._add_log_entry(f"looked at missing data - {product.get('sku')} - before checking parent skus")

        if is_variation and parent_skus:
            for parent_sku in parent_skus:
                structured['configurable_parent_sku'] = parent_sku
                AmazonImportRelationship.objects.get_or_create(
                    import_process=self.import_process,
                    parent_sku=parent_sku,
                    child_sku=structured["sku"],
                    multi_tenant_company=self.import_process.multi_tenant_company,
                )

        self._set_start_time(f"process_product_item for sku: {product.get('sku')} - before creating ImportProductInstance.")

        instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=rule,
            sales_channel=self.sales_channel,
            instance=product_instance,
            update_current_rule=True
        )

        if structured.get("type") == CONFIGURABLE:
            instance.update_only = False
        else:
            instance.update_only = self.import_process.update_only

        instance.prepare_mirror_model_class(
            mirror_model_class=AmazonProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={
                "remote_sku": structured["sku"],
                "is_variation": is_variation,
            },
        )
        instance.language = language

        try:
            instance.process()
        except IntegrityError as e:
            self._add_broken_record(
                code=self.ERROR_BROKEN_IMPORT_PROCESS,
                message="Broken import process for SKU",
                data=structured,
                context={
                    "sku": structured.get("sku"),
                    "region": getattr(view, "api_region_code", None),
                    "is_variation": is_variation,
                },
                exc=e,
            )

            if remote_product:
                # if that is already existent we can just continue with the existent one (no need to bre recreated)
                # instead
                instance.remote_instance = remote_product
            else:
                return

        self._add_log_entry("processing ImportProductInstance")

        self.update_remote_product(instance, product, view, is_variation)
        self.handle_ean_code(instance)

        if missing_data:
            # sometimes the import send absolutely empty products just the sku
            # we still want to create the variation but that one fail on handle_attributes so we will just not
            # do that and add as a broken record instead
            self._add_broken_record(
                code=self.ERROR_MISSING_DATA,
                message="Missing attributes, summaries or product type",
                data=structured,
                context={"sku": structured.get("sku"), "asin": structured.get("__asin")},
            )
        else:
            self.handle_attributes(instance)

        self._set_start_time(f"process_product_item for sku: {product.get('sku')} - before handling translations, prices and images")

        self.handle_translations(instance)
        self.handle_prices(instance)
        self.handle_images(instance)
        self.handle_documents(import_instance=instance)

        self._add_log_entry("handling translations, prices and images")

        if structured['type'] == CONFIGURABLE:
            try:
                self.handle_variations(instance, view)
            except ValueError as e:
                # if product doesn't have any rule (because it was not mapped and is a new product type)
                # this will fail here because it need the rule to create the remote configurator
                self._add_broken_record(
                    code=self.ERROR_NO_MAPPED_PRODUCT_TYPE,
                    message="No mapped product type",
                    data=structured,
                    context={"sku": structured.get("sku"), "asin": structured.get("__asin")},
                    exc=e,
                )

        if not is_variation:
            self.handle_sales_channels_views(instance, structured, view)

        self.handle_gtin_exemption(instance, view)
        self.handle_product_browse_node(instance, view)

        FetchRemoteIssuesFactory(
            remote_product=instance.remote_instance,
            view=view,
            response_data=product
        ).run()

        product_obj = product_instance or instance.instance
        if product_obj:
            data_obj, _ = AmazonImportData.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                product=product_obj,
                view=view,
            )

            data_obj.data = ensure_serializable(product)
            data_obj.save()

    def import_products_process(self):
        for product in self.get_products_data():
            self.process_product_item(product)
            self.update_percentage()


class AmazonProductItemFactory(AmazonProductsImportProcessor):
    """Process a single product in an async task."""

    def __init__(
        self,
        product_data,
        import_process,
        sales_channel,
        is_last=False,
        updated_with=None,
        language=None,
    ):
        super().__init__(import_process=import_process, sales_channel=sales_channel, language=language)
        self.product_data = product_data
        self.is_last = is_last
        self.updated_with = updated_with

    @timeit_and_log(logger, "AmazonProductItemFactory.run")
    def run(self):
        self.disable_inspector_signals()
        try:
            self.process_product_item(self.product_data)
        except UpdateOnlyInstanceNotFound as exc:
            self._add_broken_record(
                code=self.ERROR_UPDATE_ONLY_NOT_FOUND,
                message=str(exc),
                data=self.product_data,
            )
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


class AmazonConfigurableVariationsFactory:
    """Factory to create ConfigurableVariation links after import."""

    def __init__(self, import_process):
        self.import_process = import_process

    def run(self):
        from products.models import Product, ConfigurableVariation
        from sales_channels.integrations.amazon.models.imports import AmazonImportRelationship

        mtc = self.import_process.multi_tenant_company
        mapping = {}
        for rel in AmazonImportRelationship.objects.filter(import_process=self.import_process):
            mapping.setdefault(rel.parent_sku, set()).add(rel.child_sku)

        for parent_sku, children_skus in mapping.items():
            parent = Product.objects.filter(sku=parent_sku, multi_tenant_company=mtc).first()
            if not parent or not parent.is_configurable():
                continue
            children = Product.objects.filter(sku__in=list(children_skus), multi_tenant_company=mtc)
            for child in children:
                ConfigurableVariation.objects.get_or_create(
                    parent=parent,
                    variation=child,
                    multi_tenant_company=mtc,
                )


class AmazonProductsAsyncImportProcessor(AsyncProductImportMixin, AmazonProductsImportProcessor):
    """Async variant of the Amazon product importer."""

    def dispatch_task(self, data, is_last=False, updated_with=None):
        from sales_channels.integrations.amazon.tasks import amazon_product_import_item_task

        task_kwargs = {
            "import_process_id": self.import_process.id,
            "sales_channel_id": self.sales_channel.id,
            "product_data": data,
            "is_last": is_last,
            "updated_with": updated_with,
        }

        amazon_product_import_item_task(**task_kwargs)
