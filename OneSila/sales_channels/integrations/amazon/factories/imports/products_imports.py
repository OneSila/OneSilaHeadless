from decimal import Decimal

from imports_exports.factories.imports import ImportMixin
from imports_exports.factories.products import ImportProductInstance
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductType,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannelView,
    AmazonSalesChannelViewAssign,
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
            price_info = offer.price or {}
            amount = price_info.get("amount")
            currency = price_info.get("currency_code")
            if amount is not None and currency:
                prices.append({
                    "price": Decimal(amount),
                    "currency": currency,
                })
        return prices

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

    def _parse_attributes(self, product):
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
            if remote_property.type in [remote_property.TYPES.SELECT, remote_property.TYPES.MULTISELECT]:
                select_value = AmazonPropertySelectValue.objects.filter(
                    amazon_property=remote_property,
                    remote_value=value,
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

    def get_structured_product_data(self, product):
        summary = self._get_summary(product)
        asin = summary.get("asin")
        name = summary.get("item_name")
        status = summary.get("status") or []
        sku = product.sku

        product_type_code = summary.get("product_type")
        rule = None
        if product_type_code:
            rule = AmazonProductType.objects.filter(
                sales_channel=self.sales_channel,
                product_type_code=product_type_code,
            ).first()
            if rule:
                rule = rule.local_instance

        structured = {
            "name": name,
            "sku": sku,
            "active": "BUYABLE" in status,
            "product_type": rule,
        }

        structured["prices"] = self._parse_prices(product)
        structured["images"] = self._parse_images(product)
        attributes, mirror_map = self._parse_attributes(product)
        if attributes:
            structured["properties"] = attributes
            structured["__mirror_product_properties_map"] = mirror_map

        structured["translations"] = []  # Placeholder for future extension

        structured["__asin"] = asin
        structured["__issues"] = product.issues or []
        structured["__marketplace_id"] = summary.get("marketplace_id")

        return structured

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
                assign, _ = AmazonSalesChannelViewAssign.objects.get_or_create(
                    sales_channel_view=view,
                    product=import_instance.instance,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    defaults={"remote_product": remote_product},
                )
                if issues:
                    assign.issues = issues
                    assign.save()

    def import_products_process(self):
        for product in self.get_products_data():
            structured = self.get_structured_product_data(product)
            instance = ImportProductInstance(
                structured,
                import_process=self.import_process,
                rule=structured.get("product_type"),
                sales_channel=self.sales_channel,
            )
            self.update_import_instance_before_process(instance)
            instance.process()
            self.update_product_log_instance(instance.log_instance, instance)
            self.update_percentage()

