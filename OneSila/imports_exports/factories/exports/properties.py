from django.db.models import Prefetch

from properties.models import Property, PropertySelectValue, ProductPropertiesRule

from .helpers import (
    filter_queryset_by_ids,
    serialize_property_data,
    serialize_property_select_value_data,
    to_bool,
)
from .mixins import AbstractExportFactory


class PropertiesExportFactory(AbstractExportFactory):
    kind = "properties"
    supported_columns = (
        "id",
        "name",
        "internal_name",
        "type",
        "is_public_information",
        "add_to_filters",
        "has_image",
        "is_product_type",
        "translations",
        "property_select_values",
    )
    default_columns = (
        "name",
        "internal_name",
        "type",
        "is_public_information",
        "add_to_filters",
        "has_image",
        "is_product_type",
        "translations",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        queryset = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).prefetch_related(
            "propertytranslation_set",
            Prefetch(
                "propertyselectvalue_set",
                queryset=PropertySelectValue.objects.prefetch_related(
                    "propertyselectvaluetranslation_set",
                ),
            ),
        )
        return filter_queryset_by_ids(queryset=queryset, ids=ids)

    def serialize_property(self, *, property_instance):
        include_translations = self.include_column(key="translations")
        payload = {}
        base_payload = serialize_property_data(
            property_instance=property_instance,
            include_translations=include_translations,
            language=self.language,
        )

        for key in (
            "name",
            "internal_name",
            "type",
            "is_public_information",
            "add_to_filters",
            "has_image",
            "is_product_type",
            "translations",
        ):
            if key in base_payload and self.include_column(key=key):
                payload[key] = base_payload[key]

        if self.include_column(key="id"):
            payload["id"] = property_instance.id

        if self.include_column(key="property_select_values"):
            payload["property_select_values"] = [
                serialize_property_select_value_data(
                    select_value=select_value,
                    language=self.language,
                    values_are_ids=to_bool(
                        value=self.get_nested_parameter(
                            key="property_select_values",
                            nested_key="add_value_ids",
                            default=False,
                        ),
                    ),
                    include_translations=include_translations,
                    include_property_data=False,
                    include_id=self.include_column(key="id"),
                )
                for select_value in property_instance.propertyselectvalue_set.all()
            ]

        return payload

    def get_payload(self):
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        payload = []
        for index, property_instance in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            payload.append(
                self.serialize_property(property_instance=property_instance)
            )
            self.update_progress(processed=index, total_records=total_records)
        return payload


class PropertySelectValuesExportFactory(AbstractExportFactory):
    kind = "property_select_values"
    supported_columns = (
        "id",
        "value",
        "property_data",
        "translations",
    )
    default_columns = (
        "value",
        "property_data",
        "translations",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        property_ids = self.normalize_ids(value=self.get_parameter(key="property"))

        queryset = PropertySelectValue.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related(
            "property",
        ).prefetch_related(
            "propertyselectvaluetranslation_set",
            "property__propertytranslation_set",
        )

        queryset = filter_queryset_by_ids(queryset=queryset, ids=ids)
        if property_ids:
            queryset = queryset.filter(property_id__in=property_ids)

        return queryset.order_by("property_id", "id")

    def get_payload(self):
        include_translations = self.include_column(key="translations")
        include_property_data = self.include_column(key="property_data")
        values_are_ids = to_bool(
            value=self.get_parameter(key="add_value_ids") or self.get_parameter(key="values_are_ids"),
            default=False,
        )
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        payload = []
        for index, select_value in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            payload.append(
                serialize_property_select_value_data(
                    select_value=select_value,
                    language=self.language,
                    values_are_ids=values_are_ids,
                    include_translations=include_translations,
                    include_property_data=include_property_data,
                    include_id=self.include_column(key="id"),
                )
            )
            self.update_progress(processed=index, total_records=total_records)
        return payload


class RulesExportFactory(AbstractExportFactory):
    kind = "rules"
    supported_columns = (
        "value",
        "require_ean_code",
        "items",
    )
    default_columns = supported_columns

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        sales_channel = self.resolve_sales_channel()
        queryset = ProductPropertiesRule.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related(
            "product_type",
            "product_type__property",
            "sales_channel",
        ).prefetch_related(
            "product_type__propertyselectvaluetranslation_set",
            "items__property__propertytranslation_set",
        )

        queryset = filter_queryset_by_ids(queryset=queryset, ids=ids)
        if sales_channel is not None:
            queryset = queryset.filter(sales_channel=sales_channel)

        return queryset.order_by("id")

    def serialize_item(self, *, item):
        payload = {
            "type": item.type,
        }
        if item.sort_order is not None:
            payload["sort_order"] = item.sort_order
        payload["property_data"] = serialize_property_data(
            property_instance=item.property,
            include_translations=True,
            language=self.language,
        )
        return payload

    def get_payload(self):
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        payload = []
        for index, rule in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            row = {
                "value": rule.product_type.value_by_language_code(language=self.language),
            }
            if self.include_column(key="require_ean_code"):
                row["require_ean_code"] = rule.require_ean_code
            if self.include_column(key="items"):
                row["items"] = [
                    self.serialize_item(item=item)
                    for item in rule.items.all()
                ]
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload
