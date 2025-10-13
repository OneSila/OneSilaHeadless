from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import (
    filter,
    SearchFilterMixin,
    ExcluideDemoDataFilterMixin,
    lazy,
)
from strawberry_django import filter_field as custom_filter
from properties.models import Property, ProductProperty, \
    ProductProperty, PropertySelectValue, PropertyTranslation, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductPropertiesRuleItem
from django.db.models import Q, F, Count, Exists, OuterRef
from core.managers import QuerySet
from strawberry import UNSET


@filter(Property)
class PropertyFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    is_public_information: auto
    is_product_type: auto
    type: auto
    internal_name: auto

    @custom_filter
    def used_in_products(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            usage_qs = ProductProperty._base_manager.filter(
                property_id=OuterRef("pk"),
                multi_tenant_company_id=OuterRef("multi_tenant_company_id"),
            )
            queryset = queryset.annotate(
                has_usage=Exists(usage_qs)
            ).filter(has_usage=value)

        return queryset, Q()

    @custom_filter
    def missing_main_translation(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            condition = Q(
                propertytranslation__language=F("multi_tenant_company__language")
            ) & ~Q(propertytranslation__name="")
            if value:
                queryset = queryset.exclude(condition)
            else:
                queryset = queryset.filter(condition)

            queryset = queryset.distinct()

        return queryset, Q()

    @custom_filter
    def missing_translations(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            languages = queryset.values_list(
                "multi_tenant_company__languages", flat=True
            ).first() or []
            required_count = len(languages)

            queryset = queryset.annotate(
                translations_count=Count(
                    "propertytranslation__language", distinct=True
                )
            )

            if value:
                queryset = queryset.filter(translations_count__lt=required_count)
            else:
                queryset = queryset.filter(translations_count=required_count)

        return queryset, Q()


@filter(PropertySelectValue)
class PropertySelectValueFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    property: Optional[PropertyFilter]
    image: Optional[lazy['ImageFilter', "media.schema.types.filters"]]

    @custom_filter
    def used_in_products(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        if value not in (None, UNSET):
            usage_qs = ProductProperty._base_manager.filter(
                Q(value_select_id=OuterRef("pk"))
                | Q(value_multi_select=OuterRef("pk")),
                multi_tenant_company_id=OuterRef("multi_tenant_company_id"),
            )
            queryset = queryset.annotate(
                has_usage=Exists(usage_qs)
            ).filter(has_usage=value)

        return queryset, Q()

    @custom_filter
    def is_product_type(self, queryset, value: bool, prefix: str):
        if value not in (None, UNSET):
            queryset = queryset.filter(property__is_product_type=value)

        return queryset, Q()

    @custom_filter
    def missing_main_translation(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            condition = Q(
                propertyselectvaluetranslation__language=F(
                    "multi_tenant_company__language"
                )
            ) & ~Q(propertyselectvaluetranslation__value="")
            if value:
                queryset = queryset.exclude(condition)
            else:
                queryset = queryset.filter(condition)

            queryset = queryset.distinct()

        return queryset, Q()

    @custom_filter
    def missing_translations(
        self,
        queryset: QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[QuerySet, Q]:

        if value not in (None, UNSET):
            languages = queryset.values_list(
                "multi_tenant_company__languages", flat=True
            ).first() or []
            required_count = len(languages)

            queryset = queryset.annotate(
                translations_count=Count(
                    "propertyselectvaluetranslation__language", distinct=True
                )
            )

            if value:
                queryset = queryset.filter(translations_count__lt=required_count)
            else:
                queryset = queryset.filter(translations_count=required_count)

        return queryset, Q()


@filter(PropertySelectValueTranslation)
class PropertySelectValueTranslationFilter:
    id: auto
    value: auto
    propertyselectvalue: Optional[PropertySelectValueFilter]


@filter(ProductProperty)
class ProductPropertyFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    product: Optional[lazy['ProductFilter', "products.schema.types.filters"]]
    property: Optional[PropertyFilter]
    value_boolean: auto
    value_int: auto
    value_date: auto
    value_datetime: auto
    value_select: Optional[PropertySelectValueFilter]
    value_multi_select: Optional[PropertySelectValueFilter]


@filter(PropertyTranslation)
class PropertyTranslationFilter:
    id: auto
    property: Optional[PropertyFilter]


@filter(ProductPropertyTextTranslation)
class ProductPropertyTextTranslationFilter:
    id: auto
    language: auto
    product_property: Optional[ProductPropertyFilter]


@filter(ProductPropertiesRule)
class ProductPropertiesRuleFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    product_type: Optional[PropertyFilter]


@filter(ProductPropertiesRuleItem)
class ProductPropertiesRuleItemFilter(ExcluideDemoDataFilterMixin):
    id: auto
    rule: Optional[ProductPropertiesRuleFilter]
    property: Optional[PropertyFilter]
    type: auto
