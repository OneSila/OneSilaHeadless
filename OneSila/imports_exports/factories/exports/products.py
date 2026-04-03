from django.db.models import Prefetch, Q

from eancodes.models import EanCode
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation, BundleVariation, Product, ProductTranslation
from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem, ProductProperty
from sales_channels.models import SalesChannelViewAssign
from sales_prices.models import SalesPrice, SalesPriceListItem

from .helpers import (
    get_product_translation_payloads,
    serialize_sales_channel_payload,
    serialize_property_data,
    to_bool,
)
from .mixins import AbstractExportFactory
from .product_properties import ProductPropertiesExportFactory


class ProductsExportFactory(AbstractExportFactory):
    kind = "products"
    supported_columns = (
        "name",
        "sku",
        "type",
        "active",
        "vat_rate",
        "ean_code",
        "allow_backorder",
        "product_type",
        "translations",
        "sales_channels",
        "properties",
        "images",
        "documents",
        "prices",
        "sales_pricelist_items",
        "variations",
        "bundle_variations",
        "alias_variations",
        "configurator_select_values",
        "configurable_products_skus",
        "bundle_products_skus",
        "alias_products_skus",
    )
    default_columns = (
        "name",
        "sku",
        "type",
        "active",
        "vat_rate",
        "ean_code",
        "allow_backorder",
        "product_type",
        "translations",
        "sales_channels",
    )

    def validate(self):
        super().validate()
        self.assert_language_supported()

    def _needs_translations_prefetch(self):
        return self.include_column(key="name") or self.include_column(key="translations")

    def _needs_product_properties_prefetch(self):
        return (
            self.include_column(key="product_type")
            or self.include_column(key="properties")
            or self.include_column(key="configurator_select_values")
        )

    def _needs_sales_channel_assignments_prefetch(self):
        return self.include_column(key="sales_channels")

    def _needs_parent_sales_channel_assignments_prefetch(self):
        return self.include_column(key="sales_channels")

    def _needs_media_prefetch(self):
        return self.include_column(key="images") or self.include_column(key="documents")

    def _needs_sales_prices_prefetch(self):
        return self.include_column(key="prices")

    def _needs_sales_pricelist_items_prefetch(self):
        return self.include_column(key="sales_pricelist_items")

    def _needs_configurable_variations_prefetch(self):
        return (
            self.include_column(key="configurable_products_skus")
            or self.include_column(key="variations")
            or self.include_column(key="configurator_select_values")
        )

    def _needs_bundle_variations_prefetch(self):
        return (
            self.include_column(key="bundle_products_skus")
            or self.include_column(key="bundle_variations")
        )

    def _needs_alias_products_prefetch(self):
        return (
            self.include_column(key="alias_products_skus")
            or self.include_column(key="alias_variations")
        )

    def _needs_ean_codes_prefetch(self):
        return self.include_column(key="ean_code")

    def get_queryset(self):
        ids = self.normalize_ids(
            value=(
                self.get_parameter(key="product_ids")
                or self.get_parameter(key="products_ids")
                or self.get_parameter(key="ids")
            ),
        )
        sales_channel = self.resolve_sales_channel()
        active_only = to_bool(
            value=self.get_parameter(key="active") or self.get_parameter(key="active_only"),
            default=False,
        )

        queryset = Product.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        )

        select_related_fields = []
        prefetches = []

        if self.include_column(key="vat_rate"):
            select_related_fields.append("vat_rate")

        if self._needs_parent_sales_channel_assignments_prefetch():
            select_related_fields.append("alias_parent_product")

        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)

        if self._needs_translations_prefetch():
            prefetches.append(
                Prefetch(
                    "translations",
                    queryset=ProductTranslation.objects.select_related("sales_channel").prefetch_related("bullet_points"),
                )
            )

        if self._needs_sales_channel_assignments_prefetch():
            prefetches.append(
                Prefetch(
                    "saleschannelviewassign_set",
                    queryset=SalesChannelViewAssign.objects.select_related(
                        "sales_channel",
                        "sales_channel_view",
                    ),
                )
            )

        if self._needs_product_properties_prefetch():
            prefetches.append(
                Prefetch(
                    "productproperty_set",
                    queryset=ProductProperty.objects.select_related(
                        "property",
                        "value_select",
                    ).prefetch_related(
                        "value_multi_select",
                        "value_select__propertyselectvaluetranslation_set",
                        "property__propertytranslation_set",
                        "productpropertytexttranslation_set",
                    ),
                )
            )

        if self._needs_parent_sales_channel_assignments_prefetch():
            prefetches.append(
                Prefetch(
                    "configurablevariation_through_variations",
                    queryset=ConfigurableVariation.objects.select_related("parent").prefetch_related(
                        Prefetch(
                            "parent__saleschannelviewassign_set",
                            queryset=SalesChannelViewAssign.objects.select_related(
                                "sales_channel",
                                "sales_channel_view",
                            ),
                        ),
                    ),
                )
            )
            prefetches.append(
                Prefetch(
                    "bundlevariation_through_variations",
                    queryset=BundleVariation.objects.select_related("parent").prefetch_related(
                        Prefetch(
                            "parent__saleschannelviewassign_set",
                            queryset=SalesChannelViewAssign.objects.select_related(
                                "sales_channel",
                                "sales_channel_view",
                            ),
                        ),
                    ),
                )
            )
            prefetches.append(
                Prefetch(
                    "alias_parent_product__saleschannelviewassign_set",
                    queryset=SalesChannelViewAssign.objects.select_related(
                        "sales_channel",
                        "sales_channel_view",
                    ),
                )
            )

        if self._needs_media_prefetch():
            prefetches.append(
                Prefetch(
                    "mediaproductthrough_set",
                    queryset=MediaProductThrough.objects.select_related(
                        "media",
                        "media__document_type",
                        "sales_channel",
                    ),
                )
            )

        if self._needs_sales_prices_prefetch():
            prefetches.append(
                Prefetch(
                    "salesprice_set",
                    queryset=SalesPrice.objects.select_related("currency"),
                )
            )

        if self._needs_sales_pricelist_items_prefetch():
            prefetches.append(
                Prefetch(
                    "salespricelistitem_set",
                    queryset=SalesPriceListItem.objects.select_related(
                        "salespricelist",
                        "salespricelist__currency",
                    ),
                )
            )

        if self._needs_configurable_variations_prefetch():
            prefetches.append("configurable_variations")

        if self._needs_bundle_variations_prefetch():
            prefetches.append("bundle_variations")

        if self._needs_alias_products_prefetch():
            prefetches.append("alias_products")

        if self._needs_ean_codes_prefetch():
            prefetches.append("eancode_set")

        if prefetches:
            queryset = queryset.prefetch_related(*prefetches)

        if ids:
            queryset = queryset.filter(id__in=ids)

        if active_only:
            queryset = queryset.filter(active=True)

        if sales_channel is not None:
            queryset = queryset.filter(
                Q(saleschannelviewassign__sales_channel_view__sales_channel=sales_channel)
                | Q(configurablevariation_through_variations__parent__saleschannelviewassign__sales_channel_view__sales_channel=sales_channel)
                | Q(bundlevariation_through_variations__parent__saleschannelviewassign__sales_channel_view__sales_channel=sales_channel)
                | Q(alias_parent_product__saleschannelviewassign__sales_channel_view__sales_channel=sales_channel)
            ).distinct()

        return queryset.order_by("id")

    def build_rule_cache(self, *, queryset):
        product_type_ids = set(
            ProductProperty.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                product__in=queryset.values("id"),
                property__is_product_type=True,
                value_select_id__isnull=False,
            ).values_list("value_select_id", flat=True).distinct()
        )

        if not product_type_ids:
            return {}

        sales_channel = self.resolve_sales_channel()
        queryset = ProductPropertiesRule.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product_type_id__in=product_type_ids,
            sales_channel__in=[sales_channel, None] if sales_channel else [None],
        ).prefetch_related(
            "items",
        )
        rules = list(queryset)

        cache = {}
        for product_type_id in product_type_ids:
            preferred_rule = None
            fallback_rule = None
            for rule in rules:
                if rule.product_type_id != product_type_id:
                    continue
                if sales_channel and rule.sales_channel_id == sales_channel.id:
                    preferred_rule = rule
                    break
                if rule.sales_channel_id is None:
                    fallback_rule = rule
            cache[product_type_id] = preferred_rule or fallback_rule
        return cache

    def get_prefetched_related_objects(self, *, instance, relation_name):
        prefetched = getattr(instance, "_prefetched_objects_cache", {})
        if relation_name in prefetched:
            return prefetched[relation_name]
        return list(getattr(instance, relation_name).all())

    def get_product_rule(self, *, product, rule_cache):
        for product_property in product.productproperty_set.all():
            if product_property.property.is_product_type and product_property.value_select_id:
                return rule_cache.get(product_property.value_select_id)
        return None

    def serialize_product_properties(self, *, product, rule):
        exporter = ProductPropertiesExportFactory(
            export_process=self.export_process,
            columns=["properties"],
        )
        return exporter.serialize_product_properties(product=product, rule=rule)

    def get_ean_code(self, *, product):
        ean_codes = self.get_prefetched_related_objects(
            instance=product,
            relation_name="eancode_set",
        )
        if not ean_codes:
            return None
        return ean_codes[0].ean_code

    def get_product_type_value(self, *, product, rule):
        if rule is not None:
            return rule.product_type.value_by_language_code(language=self.language)
        for product_property in product.productproperty_set.all():
            if product_property.property.is_product_type and product_property.value_select:
                return product_property.value_select.value_by_language_code(language=self.language)
        return None

    def get_media_assignments(self, *, product):
        sales_channel = self.resolve_sales_channel()
        assignments = list(product.mediaproductthrough_set.all())
        if sales_channel is None:
            return [assignment for assignment in assignments if assignment.sales_channel_id is None]

        channel_specific = [
            assignment
            for assignment in assignments
            if assignment.sales_channel_id == sales_channel.id
        ]
        if channel_specific:
            return channel_specific

        return [assignment for assignment in assignments if assignment.sales_channel_id is None]

    def get_product_sales_channels(self, *, product):
        sales_channels_by_id = {}

        def add_assignments(*, assignments):
            for assignment in assignments:
                sales_channel = assignment.sales_channel or getattr(
                    assignment.sales_channel_view,
                    "sales_channel",
                    None,
                )
                if sales_channel is None:
                    continue
                sales_channels_by_id[sales_channel.id] = sales_channel

        add_assignments(assignments=product.saleschannelviewassign_set.all())

        for relation in product.configurablevariation_through_variations.all():
            add_assignments(assignments=relation.parent.saleschannelviewassign_set.all())

        for relation in product.bundlevariation_through_variations.all():
            add_assignments(assignments=relation.parent.saleschannelviewassign_set.all())

        if product.alias_parent_product_id:
            add_assignments(assignments=product.alias_parent_product.saleschannelviewassign_set.all())

        sales_channels = list(sales_channels_by_id.values())
        sales_channels.sort(key=lambda sales_channel: (sales_channel.hostname, sales_channel.id))
        return [
            serialize_sales_channel_payload(sales_channel=sales_channel)
            for sales_channel in sales_channels
        ]

    def serialize_media(self, *, product):
        images = []
        documents = []
        for assignment in self.get_media_assignments(product=product):
            media = assignment.media
            if media.type == Media.IMAGE:
                images.append(
                    {
                        "image_url": media.image_url(),
                        "type": media.image_type,
                        "title": media.title,
                        "description": media.description,
                        "is_main_image": assignment.is_main_image,
                        "sort_order": assignment.sort_order,
                    }
                )
            elif media.type == Media.FILE:
                documents.append(
                    {
                        "document_url": media.get_real_document_file(),
                        "title": media.title,
                        "description": media.description,
                        "document_type": media.document_type.code if media.document_type_id else None,
                        "document_language": media.document_language,
                        "sort_order": assignment.sort_order,
                        "thumbnail_image": media.document_image_thumbnail_url(),
                        "is_document_image": media.is_document_image,
                    }
                )
        return images, documents

    def serialize_prices(self, *, product):
        prices = []
        for sales_price in product.salesprice_set.all():
            prices.append(
                {
                    "rrp": sales_price.rrp,
                    "price": sales_price.price,
                    "currency": sales_price.currency.iso_code,
                }
            )
        return prices

    def serialize_sales_pricelist_items(self, *, product):
        items = []
        for item in product.salespricelistitem_set.all():
            items.append(
                {
                    "salespricelist_data": {
                        "name": item.salespricelist.name,
                        "currency": item.salespricelist.currency.iso_code,
                        "start_date": item.salespricelist.start_date,
                        "end_date": item.salespricelist.end_date,
                    },
                    "price_auto": item.price_auto,
                    "discount_auto": item.discount_auto,
                    "price_override": item.price_override,
                    "discount_override": item.discount_override,
                }
            )
        return items

    def serialize_configurator_select_values(self, *, product, rule):
        if rule is None or not product.is_configurable():
            return []

        property_ids = [
            item.property_id
            for item in rule.items.all()
            if item.type in (
                ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
            )
        ]
        if not property_ids:
            return []

        values = []
        seen = set()
        for variation in product.get_unique_configurable_variations():
            variation_properties = self.get_prefetched_related_objects(
                instance=variation,
                relation_name="productproperty_set",
            )
            for product_property in variation_properties:
                if product_property.property_id not in property_ids:
                    continue
                if not product_property.value_select_id:
                    continue
                key = (product_property.property_id, product_property.value_select_id)
                if key in seen:
                    continue
                seen.add(key)
                values.append(
                    {
                        "property_data": serialize_property_data(
                            property_instance=product_property.property,
                            include_translations=True,
                            language=self.language,
                        ),
                        "value": product_property.value_select.value_by_language_code(language=self.language),
                    }
                )
        return values

    def serialize_variation_payload(self, *, variation, flat=False):
        payload = {
            "sku": variation.sku,
            "type": variation.type,
        }
        if variation.active is not None:
            payload["active"] = variation.active
        if variation.allow_backorder is not None:
            payload["allow_backorder"] = variation.allow_backorder
        if variation.vat_rate_id:
            payload["vat_rate"] = variation.vat_rate.rate
        ean_code = EanCode.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product=variation,
        ).first()
        if ean_code and ean_code.ean_code:
            payload["ean_code"] = ean_code.ean_code

        translations = get_product_translation_payloads(
            product=variation,
            language=self.language,
            sales_channel=self.resolve_sales_channel(),
        )
        if translations:
            payload["translations"] = translations
            payload["name"] = translations[0].get("name")

        if not flat:
            rule = variation.get_product_rule(sales_channel=self.resolve_sales_channel())
            if rule is not None:
                payload["product_type"] = rule.product_type.value_by_language_code(language=self.language)

        return payload

    def serialize_product(self, *, product, rule, nested=False):
        flat = to_bool(value=self.get_parameter(key="flat"), default=True)
        row = {}
        translations = get_product_translation_payloads(
            product=product,
            language=self.language,
            sales_channel=self.resolve_sales_channel(),
        )

        if self.include_column(key="name"):
            if translations:
                row["name"] = translations[0]["name"]
            else:
                row["name"] = product.name
        if self.include_column(key="sku"):
            row["sku"] = product.sku
        if self.include_column(key="type"):
            row["type"] = product.type
        if self.include_column(key="active"):
            row["active"] = product.active
        if self.include_column(key="vat_rate"):
            row["vat_rate"] = product.vat_rate.rate if product.vat_rate_id else None
        if self.include_column(key="ean_code"):
            row["ean_code"] = self.get_ean_code(product=product)
        if self.include_column(key="allow_backorder"):
            row["allow_backorder"] = product.allow_backorder
        if self.include_column(key="product_type"):
            row["product_type"] = self.get_product_type_value(product=product, rule=rule)
        if self.include_column(key="translations"):
            row["translations"] = translations
        if self.include_column(key="sales_channels"):
            row["sales_channels"] = self.get_product_sales_channels(product=product)
        if self.include_column(key="properties"):
            row["properties"] = self.serialize_product_properties(product=product, rule=rule)

        images, documents = self.serialize_media(product=product)
        if self.include_column(key="images"):
            row["images"] = images
        if self.include_column(key="documents"):
            row["documents"] = documents
        if self.include_column(key="prices"):
            row["prices"] = self.serialize_prices(product=product)
        if self.include_column(key="sales_pricelist_items"):
            row["sales_pricelist_items"] = self.serialize_sales_pricelist_items(product=product)

        if nested:
            return row

        if flat:
            if self.include_column(key="configurable_products_skus"):
                row["configurable_products_skus"] = [
                    variation.sku
                    for variation in self.get_prefetched_related_objects(
                        instance=product,
                        relation_name="configurable_variations",
                    )
                ]
            if self.include_column(key="bundle_products_skus"):
                row["bundle_products_skus"] = [
                    variation.sku
                    for variation in self.get_prefetched_related_objects(
                        instance=product,
                        relation_name="bundle_variations",
                    )
                ]
            if self.include_column(key="alias_products_skus"):
                row["alias_products_skus"] = [
                    alias_product.sku
                    for alias_product in self.get_prefetched_related_objects(
                        instance=product,
                        relation_name="alias_products",
                    )
                ]
            return row

        if self.include_column(key="variations") and product.is_configurable():
            row["variations"] = [
                {
                    "variation_data": self.serialize_variation_payload(
                        variation=variation,
                        flat=False,
                    ),
                }
                for variation in product.get_unique_configurable_variations(
                    sales_channel=self.resolve_sales_channel(),
                )
            ]

        if self.include_column(key="bundle_variations") and product.is_bundle():
            row["bundle_variations"] = [
                {
                    "variation_data": self.serialize_variation_payload(
                        variation=bundle_variation.variation,
                        flat=False,
                    ),
                    "quantity": bundle_variation.quantity,
                }
                for bundle_variation in product.bundlevariation_through_parents.select_related("variation")
            ]

        if self.include_column(key="alias_variations"):
            row["alias_variations"] = [
                {
                    "variation_data": self.serialize_variation_payload(
                        variation=alias_product,
                        flat=False,
                    ),
                }
                for alias_product in product.alias_products.all()
            ]

        if self.include_column(key="configurator_select_values"):
            row["configurator_select_values"] = self.serialize_configurator_select_values(
                product=product,
                rule=rule,
            )

        return row

    def get_payload(self):
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        rule_cache = self.build_rule_cache(queryset=queryset)
        payload = []
        for index, product in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            payload.append(
                self.serialize_product(
                    product=product,
                    rule=self.get_product_rule(product=product, rule_cache=rule_cache),
                )
            )
            self.update_progress(processed=index, total_records=total_records)
        return payload
