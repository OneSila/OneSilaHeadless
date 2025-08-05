import pprint
from decimal import Decimal
from django.utils import timezone
import logging
import traceback
from django.db import IntegrityError
from core.decorators import timeit_and_log
from imports_exports.factories.imports import ImportMixin, AsyncProductImportMixin
from imports_exports.factories.products import ImportProductInstance
from products.models import Product
from products.product_types import SIMPLE, CONFIGURABLE
from properties.models import Property, PropertyTranslation
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.decorators import throttle_safe
from spapi import CatalogApi
from sales_channels.integrations.amazon.helpers import (
    infer_product_type,
    extract_description_and_bullets,
    get_is_product_variation, extract_amazon_attribute_value,
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
)

from sales_channels.integrations.amazon.constants import AMAZON_INTERNAL_PROPERTIES
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.models import SalesChannelViewAssign
from core.helpers import ensure_serializable
from dateutil.parser import parse
import datetime
from imports_exports.helpers import append_broken_record, increment_processed_records
from sales_channels.integrations.amazon.models.imports import AmazonImportRelationship
from core.logging_helpers import AddLogTimeentry

logger = logging.getLogger(__name__)


class AmazonProductsImportProcessor(ImportMixin, GetAmazonAPIMixin, AddLogTimeentry):
    """Basic Amazon products import processor."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_MULTIPLE_ASIN = "MULTIPLE_ASIN"
    ERROR_MISSING_DATA = "MISSING_DATA"
    ERROR_NO_MAPPED_PRODUCT_TYPE = "NO_MAPPED_PRODUCT_TYPE"
    ERROR_PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"

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

        append_broken_record(self.import_process.id, record)

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)
        self.sales_channel = sales_channel
        self.api = self.get_api()
        self.broken_records: list[dict] = []

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
        # FIXME/HELP: What is this used for? Return 0 to not have it work at all
        # for performance?
        return self.get_total_number_of_products()

    @timeit_and_log(logger, "AmazonProductsImportProcessor.get_products_data")
    def get_products_data(self):
        # Delegate to the mixin helper which yields ListingItem objects
        yield from self.get_all_products()

    # ------------------------------------------------------------------
    # Structuring
    # ------------------------------------------------------------------
    @timeit_and_log(logger, "AmazonProductsImportProcessor._get_summary")
    def _get_summary(self, product):
        summaries = product.get("summaries") or []
        return summaries[0] if summaries else {}

    def _parse_prices(self, product):
        prices = []
        for offer in product.get("offers", []):

            if offer.get("offer_type") != "B2C":
                continue

            price_info = offer.get("price") or {}
            amount = price_info.get("amount")
            currency = price_info.get("currency_code")
            if amount is not None and currency:
                prices.append({
                    "price": Decimal(amount),
                    "currency": currency,
                })

        return prices

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
        for key, values in attrs.items():
            if not key.startswith("main_product_image_locator") and not key.startswith("other_product_image_locator"):
                continue
            for value in values:
                url = value.get("media_location")
                if not url:
                    continue
                images.append({
                    "image_url": url,
                    "sort_order": index,
                    "is_main_image": index == 0,
                })
                index += 1
        return images

    @timeit_and_log(logger, "AmazonProductsImportProcessor._parse_attributes")
    def _parse_attributes(self, attributes, product_type, marketplace):
        attrs = []
        mirror_map = {}
        product_attrs = attributes or {}

        for code, values in product_attrs.items():

            if code in AMAZON_INTERNAL_PROPERTIES:
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
                        logger.error(
                            "Could not extract value for attribute '%s' (real code '%s') with entry %s",
                            code,
                            real_code,
                            values[0],
                        )
                        continue

                    if remote_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
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

                        if select_value and select_value.local_instance:
                            attrs.append({
                                "property": remote_property.local_instance,
                                "value": select_value.local_instance.id,
                                "value_is_id": True,
                            })
                            mirror_map[remote_property.local_instance.id] = {
                                "remote_property": remote_property,
                                "remote_value": value,
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

    @timeit_and_log(logger, "AmazonProductsImportProcessor.get_product_rule")
    def get_product_rule(self, product_data):
        summary = self._get_summary(product_data)
        product_type_code = summary.get("product_type")
        rule = None

        if product_type_code:
            rule = AmazonProductType.objects.filter(
                sales_channel=self.sales_channel,
                product_type_code=product_type_code,
            ).first()

            if rule:
                rule = rule.local_instance

        return rule

    def _get_language_for_marketplace(self, view):

        if not view:
            return None

        remote_lang = view.remote_languages.first()
        return remote_lang.local_instance if remote_lang else None

    @timeit_and_log(logger, "AmazonProductsImportProcessor.get__product_data")
    def get__product_data(self, product_data):
        summary = self._get_summary(product_data)
        asin = summary.get("asin")
        status = summary.get("status") or []
        sku = product_data.get("sku")
        type = infer_product_type(product_data)
        marketplace_id = summary.get("marketplace_id")

        name = summary.get("item_name")

        # it seems that sometimes the name can be None coming from Amazon. IN that case we fallback to sku
        if name is None:
            name = sku

        view = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel,
            remote_id=marketplace_id,
        ).first()
        language = self._get_language_for_marketplace(view)

        structured = {
            "name": name,
            "sku": sku,
            "active": "BUYABLE" in status,
            "type": type
        }

        structured["images"] = self._parse_images(product_data)

        if type == SIMPLE:
            structured["prices"] = self._parse_prices(product_data)

        product_type_code = summary.get("product_type")
        product_attrs = product_data.get("attributes") or {}
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
        asin_property = Property.objects.filter(
            internal_name="merchant_suggested_asin",
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        ).first()
        if asin_property and asin:
            attributes.append({
                "property": asin_property,
                "value": asin,
                "translations": [
                    {
                        "language": self.sales_channel.multi_tenant_company.language,
                        "value": asin,
                    }
                ],
            })

        if attributes:
            structured["properties"] = attributes
            structured["__mirror_product_properties_map"] = mirror_map

        structured["translations"] = self._parse_translations(name, language, product_data.get("attributes"))
        configurator_values, amazon_theme = self._parse_configurator_select_values(product_data)

        if configurator_values:
            structured["configurator_select_values"] = configurator_values

        if amazon_theme:
            structured["__amazon_theme"] = amazon_theme

        structured["__asin"] = asin
        structured["__issues"] = product_data.get("issues") or []
        structured["__marketplace_id"] = marketplace_id

        return structured, language, view

    def update_product_import_instance(self, instance: ImportProductInstance):
        instance.prepare_mirror_model_class(
            mirror_model_class=AmazonProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={"asin": instance.data.get("__asin")},
        )

    def update_remote_product(self, import_instance: ImportProductInstance, product, view, is_variation: bool):
        remote_product = import_instance.remote_instance
        asin = import_instance.data.get("__asin")

        if asin and not remote_product.remote_id:
            remote_product.remote_id = asin

        sku = product.get("sku")
        if sku and not remote_product.remote_sku:
            remote_product.remote_sku = sku

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation

        if view.remote_id not in (remote_product.created_marketplaces or []):
            remote_product.created_marketplaces.append(view.remote_id)

        remote_product.save()

    def handle_ean_code(self, import_instance: ImportProductInstance):
        amazon_ean_code, _ = AmazonEanCode.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )

        if hasattr(import_instance, "ean_code") and import_instance.ean_code:
            if amazon_ean_code.ean_code != import_instance.ean_code:
                amazon_ean_code.ean_code = import_instance.ean_code
                amazon_ean_code.save()

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

                if updated:
                    remote_product_property.save()

    def handle_translations(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "translations"):
            AmazonProductContent.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
            )

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

    def handle_images(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, "images"):
            for image_ass in import_instance.images_associations_instances:
                AmazonImageProductAssociation.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=image_ass,
                    remote_product=import_instance.remote_instance,
                )

    def handle_variations(self, import_instance: ImportProductInstance):
        theme = import_instance.data.get("__amazon_theme")
        if not theme:
            return

        from sales_channels.models.products import RemoteProductConfigurator

        remote_product = import_instance.remote_instance
        if hasattr(remote_product, "configurator"):
            configurator = remote_product.configurator
            configurator.update_if_needed(
                rule=import_instance.rule,
                send_sync_signal=False,
                amazon_theme=theme,
            )
        else:
            RemoteProductConfigurator.objects.create_from_remote_product(
                remote_product=remote_product,
                rule=import_instance.rule,
                variations=None,
                amazon_theme=theme,
            )

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
        from sales_channels.integrations.amazon.factories.sales_channels.issues import FetchRemoteIssuesFactory
        # Kickstarting the AddLogTimeentry class settings.
        self._set_logger(logger)
        self._set_start_time()

        product_instance = None
        qs = AmazonProduct.objects.filter(
            remote_sku=product.get("sku"),
            sales_channel=self.sales_channel,
            multi_tenant_company=self.import_process.multi_tenant_company
        )
        remote_product = qs.first()

        self._add_log_entry("getting remote product")

        if remote_product:
            product_instance = remote_product.local_instance
            is_variation = remote_product.is_variation

            if is_variation:
                parent_skus = list(
                    AmazonProduct.objects
                    .filter(remote_parent_product=remote_product.remote_parent_product)
                    .values_list("remote_sku", flat=True)
                )
            else:
                parent_skus = []
        else:
            is_variation, parent_skus = get_is_product_variation(product)

        self._add_log_entry("getting parent skus")

        summary = self._get_summary(product)
        rule = self.get_product_rule(product)
        structured, language, view = self.get__product_data(product)
        missing_data = (
            not product.get("attributes")
            or not product.get("summaries")
            or not summary.get("product_type")
        )

        self._add_log_entry("getting structured data")

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

        self._add_log_entry("getting parent skus")

        if is_variation and parent_skus:

            for parent_sku in parent_skus:
                structured['configurable_parent_sku'] = parent_sku
                AmazonImportRelationship.objects.get_or_create(
                    import_process=self.import_process,
                    parent_sku=parent_sku,
                    child_sku=structured["sku"],
                )

        self._add_log_entry("getting parent skus")

        instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=rule,
            sales_channel=self.sales_channel,
            instance=product_instance,
            update_current_rule=True
        )

        self._add_log_entry("preparing ImportProductInstance")

        instance.prepare_mirror_model_class(
            mirror_model_class=AmazonProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={
                "remote_id": structured["__asin"],
                "asin": structured["__asin"],
                "remote_sku": structured["sku"],
                "is_variation": is_variation,
            },
        )
        instance.language = language

        self._add_log_entry("preparing ImportProductInstance mirror model")

        try:
            instance.process()
        except IntegrityError as e:
            # because we have this:
            # "remote_id": structured["__asin"],
            # "asin": structured["__asin"],
            # in the mirror_model_defaults it will try to create the mirror model with another asin
            # this is not possible so we will add it as a broken recored instead
            self._add_broken_record(
                code=self.ERROR_MULTIPLE_ASIN,
                message="Multiple ASINs for SKU",
                data=structured,
                context={
                    "sku": structured.get("sku"),
                    "asin": structured.get("__asin"),
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

        self._add_log_entry("updating remote product")

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

        self._add_log_entry("updating remote product")

        self.handle_translations(instance)
        self.handle_prices(instance)
        self.handle_images(instance)

        self._add_log_entry("handling translations, prices and images")

        if structured['type'] == CONFIGURABLE:
            try:
                self.handle_variations(instance)
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

            self._add_log_entry("handling variations")

        if not is_variation:
            self.handle_sales_channels_views(instance, structured, view)

            self._add_log_entry("handling sales channels views")

        FetchRemoteIssuesFactory(
            remote_product=instance.remote_instance,
            view=view,
            response_data=product
        ).run()

        self._add_log_entry("fetching remote issues")

    @timeit_and_log(logger, "AmazonProductsImportProcessor.import_products_process")
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
        try:
            self.process_product_item(self.product_data)
        except Exception as exc:  # capture unexpected errors
            self._add_broken_record(
                code="UNKNOWN_ERROR",
                message="Unexpected error while processing product",
                data=self.product_data,
                exc=exc,
            )

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
