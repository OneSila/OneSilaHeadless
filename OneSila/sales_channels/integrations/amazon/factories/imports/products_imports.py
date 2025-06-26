from decimal import Decimal

from imports_exports.factories.imports import ImportMixin
from imports_exports.factories.products import ImportProductInstance
from products.product_types import SIMPLE
from properties.models import Property
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.helpers import (
    infer_product_type,
    extract_description_and_bullets,
    get_is_product_variation,
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
from sales_channels.models import SalesChannelViewAssign


class AmazonProductsImportProcessor(ImportMixin, GetAmazonAPIMixin):
    """Basic Amazon products import processor."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)
        self.sales_channel = sales_channel
        self.api = self.get_api()
        # Mapping of child SKU to parent SKU for configurator creation
        # after all products have been imported.
        self._configurable_map: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def prepare_import_process(self):
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save(update_fields=["active", "is_importing"])

    def process_completed(self):
        self.sales_channel.active = True
        self.sales_channel.is_importing = False
        self.sales_channel.save(update_fields=["active", "is_importing"])
        self._create_configurable_variations()

    def _create_configurable_variations(self):
        """Create ConfigurableVariation links after all products are imported."""
        from products.models import Product, ConfigurableVariation

        mtc = self.import_process.multi_tenant_company
        for child_sku, parent_sku in self._configurable_map.items():
            parent = Product.objects.filter(sku=parent_sku,
                                           multi_tenant_company=mtc).first()
            child = Product.objects.filter(sku=child_sku,
                                          multi_tenant_company=mtc).first()
            if parent and parent.is_configurable() and child:
                ConfigurableVariation.objects.get_or_create(
                    parent=parent,
                    variation=child,
                    multi_tenant_company=mtc,
                )

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------
    def get_total_instances(self):
        # SP‑API does not provide a count endpoint easily; return a dummy value.
        return 100

    def get_products_data(self):
        # Delegate to the mixin helper which yields ListingItem objects
        yield from self.get_all_products()

    # ------------------------------------------------------------------
    # Structuring
    # ------------------------------------------------------------------
    def _get_summary(self, product):
        summaries = product.summaries or []
        return summaries[0] if summaries else {}

    def _parse_prices(self, product):
        prices = []
        for offer in product.offers or []:

            if offer.offer_type != "B2C":
                continue

            price_info = offer.price or {}
            amount = price_info.amount
            currency = price_info.currency_code
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
        attrs = product.attributes or {}
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

    def _parse_attributes(self, product, marketplace):
        attrs = []
        mirror_map = {}
        product_attrs = product.attributes or {}
        for code, values in product_attrs.items():
            if code in AMAZON_INTERNAL_PROPERTIES:
                continue

            remote_property = AmazonProperty.objects.filter(sales_channel=self.sales_channel, code=code).first()
            if not remote_property or not remote_property.local_instance:
                continue

            val_entry = values[0]
            value = val_entry.get("value") or val_entry.get("name")
            if remote_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
                select_value = AmazonPropertySelectValue.objects.filter(
                    amazon_property=remote_property,
                    remote_value=value,
                    marketplace=marketplace
                ).first()

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
            attrs.append({"property": remote_property.local_instance, "value": value})
            mirror_map[remote_property.local_instance.id] = {
                "remote_property": remote_property,
                "remote_value": value,
            }
        return attrs, mirror_map

    def get_product_rule(self, product_data):
        summary = self._get_summary(product_data)
        product_type_code = summary.product_type
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

    def get__product_data(self, product_data):
        summary = self._get_summary(product_data)
        asin = summary.asin
        name = summary.item_name
        status = summary.status or []
        sku = product_data.sku
        type = infer_product_type(product_data)
        marketplace_id = summary.marketplace_id

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

        if type == SIMPLE:
            structured["prices"] = self._parse_prices(product_data)
            structured["images"] = self._parse_images(product_data)

        attributes, mirror_map = self._parse_attributes(product_data, view)
        if attributes:
            structured["properties"] = attributes
            structured["__mirror_product_properties_map"] = mirror_map

        structured["translations"] = self._parse_translations(name, language, attributes)

        structured["__asin"] = asin
        structured["__issues"] = product_data.issues or []
        structured["__marketplace_id"] = marketplace_id

        return structured, language

    def update_product_import_instance(self, instance: ImportProductInstance):
        instance.prepare_mirror_model_class(
            mirror_model_class=AmazonProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={"asin": instance.data.get("__asin")},
        )

    def update_product_log_instance(self, log_instance, import_instance: ImportProductInstance):
        remote_product = import_instance.remote_instance
        log_instance.successfully_imported = True
        log_instance.remote_product = remote_product
        log_instance.save()

        marketplace_id = import_instance.data.get("__marketplace_id")
        issues = import_instance.data.get("__issues")
        if marketplace_id:
            view = AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel, remote_id=marketplace_id).first()
            if view:
                assign, _ = SalesChannelViewAssign.objects.get_or_create(
                    sales_channel_view=view,
                    product=import_instance.instance,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    defaults={"remote_product": remote_product},
                )
                if issues:
                    assign.issues = issues
                    assign.save()

    def update_remote_product(self, import_instance: ImportProductInstance, product, is_variation: bool):
        remote_product = import_instance.remote_instance
        asin = import_instance.data.get("__asin")

        if asin and not remote_product.remote_id:
            remote_product.remote_id = asin

        sku = getattr(product, "sku", None)
        if sku and not remote_product.remote_sku:
            remote_product.remote_sku = sku

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation

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
                    remote_property=remote_property,
                )

                if not remote_product_property.remote_value:
                    remote_product_property.remote_value = remote_value
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
        # Variations import will be implemented later
        pass

    def handle_sales_channels_views(self, import_instance: ImportProductInstance, product):
        marketplace_id = import_instance.data.get("__marketplace_id")
        if not marketplace_id:
            return

        view = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel,
            remote_id=marketplace_id,
        ).first()

        if not view:
            return

        SalesChannelViewAssign.objects.get_or_create(
            product=import_instance.instance,
            sales_channel_view=view,
            multi_tenant_company=self.import_process.multi_tenant_company,
            remote_product=import_instance.remote_instance,
            sales_channel=self.sales_channel,
        )

    def import_products_process(self):
        for product in self.get_products_data():
            is_variation, parent_sku = get_is_product_variation(product)
            rule = self.get_product_rule(product)
            structured, language = self.get__product_data(product)

            # Keep track of parent-child relationships to process later
            if is_variation and parent_sku:
                self._configurable_map[structured["sku"]] = parent_sku
                structured["configurable_parent_sku"] = parent_sku

            product_instance = None
            remote_product = AmazonProduct.objects.filter(
                asin=structured["__asin"],
                multi_tenant_company=self.import_process.multi_tenant_company
            ).first()
            if remote_product:
                product_instance = remote_product.local_instance

            instance = ImportProductInstance(
                structured,
                import_process=self.import_process,
                rule=rule,
                sales_channel=self.sales_channel,
                instance=product_instance  # this will skip the create
            )
            instance.prepare_mirror_model_class(
                mirror_model_class=AmazonProduct,
                sales_channel=self.sales_channel,
                mirror_model_map={"local_instance": "*"},
                mirror_model_defaults={
                    "remote_id": structured["__asin"],
                    "asin": structured["__asin"],
                    "is_variation": is_variation,
                },
            )
            instance.language = language
            instance.process()

            self.update_remote_product(instance, product, is_variation)
            self.handle_ean_code(instance)
            self.handle_attributes(instance)
            self.handle_translations(instance)
            self.handle_prices(instance)
            self.handle_images(instance)
            self.handle_variations(instance)

            if not is_variation:
                self.handle_sales_channels_views(instance, product)

            self.update_percentage()
