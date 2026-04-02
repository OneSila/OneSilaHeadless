from django.db.models import Prefetch

from products.models import Product
from properties.models import ProductPropertiesRule, ProductProperty

from .helpers import (
    build_product_stub,
    build_requirement_map,
    serialize_product_property_value,
    serialize_property_data,
    to_bool,
)
from .mixins import AbstractExportFactory


class ProductPropertiesExportFactory(AbstractExportFactory):
    kind = "product_properties"
    supported_columns = (
        "product_data",
        "product_sku",
        "properties",
    )
    default_columns = (
        "product_data",
        "properties",
    )

    def get_queryset(self):
        product_ids = self.normalize_ids(
            value=self.get_parameter(key="product") or self.get_parameter(key="product_ids"),
        )
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))

        queryset = Product.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).prefetch_related(
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
            ),
        )

        if product_ids:
            queryset = queryset.filter(id__in=product_ids)
        elif ids:
            queryset = queryset.filter(id__in=ids)

        return queryset.order_by("id")

    def build_rule_cache(self, *, products):
        product_type_ids = set()
        for product in products:
            for product_property in product.productproperty_set.all():
                if product_property.property.is_product_type and product_property.value_select_id:
                    product_type_ids.add(product_property.value_select_id)

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

    def get_product_rule(self, *, product, rule_cache):
        for product_property in product.productproperty_set.all():
            if product_property.property.is_product_type and product_property.value_select_id:
                return rule_cache.get(product_property.value_select_id)
        return None

    def serialize_product_properties(self, *, product, rule):
        include_translations = to_bool(
            value=self.get_parameter(key="add_translations"),
            default=True,
        )
        include_value_ids = to_bool(
            value=self.get_parameter(key="add_value_ids")
            or self.get_nested_parameter(
                key="product_properties",
                nested_key="add_value_ids",
                default=False,
            ),
        )
        values_are_ids = to_bool(
            value=(
                self.get_parameter(key="values_are_ids")
                or self.get_parameter(key="add_value_ids")
                or self.get_nested_parameter(
                    key="product_properties",
                    nested_key="add_value_ids",
                    default=False,
                )
            ),
            default=False,
        )
        requirement_map = build_requirement_map(rule=rule)

        payload = []
        for product_property in product.productproperty_set.all():
            if product_property.property.is_product_type:
                continue

            value, values = serialize_product_property_value(
                product_property=product_property,
                language=self.language,
                values_are_ids=values_are_ids,
                include_translations=include_translations,
                include_value_ids=include_value_ids,
            )

            row = {
                "property": serialize_property_data(
                    property_instance=product_property.property,
                    include_translations=include_translations,
                    language=self.language,
                ),
                "value": value,
                "values": values,
            }
            requirement = requirement_map.get(product_property.property_id)
            if requirement:
                row["requirement"] = requirement
            payload.append(row)

        return payload

    def get_payload(self):
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        products = list(self.iterate_queryset(queryset=queryset))
        rule_cache = self.build_rule_cache(products=products)
        include_product_data = self.include_column(key="product_data")
        include_product_sku = self.include_column(key="product_sku")

        payload = []
        for index, product in enumerate(products, start=1):
            row = {}
            if include_product_data:
                row["product_data"] = build_product_stub(product=product)
            if include_product_sku:
                row["product_sku"] = product.sku
            if self.include_column(key="properties"):
                row["properties"] = self.serialize_product_properties(
                    product=product,
                    rule=self.get_product_rule(product=product, rule_cache=rule_cache),
                )
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload
