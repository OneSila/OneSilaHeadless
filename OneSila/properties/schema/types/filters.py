from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import (
    filter,
    SearchFilterMixin,
    ExcluideDemoDataFilterMixin,
)
from media.schema.types.filters import ImageFilter
from strawberry_django import filter_field as custom_filter
from properties.models import Property, ProductProperty, \
    ProductProperty, PropertySelectValue, PropertyTranslation, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductPropertiesRuleItem
from products.schema.types.filters import ProductFilter
from django.db.models import Q, F
from core.managers import QuerySet
from strawberry import UNSET


@filter(Property)
class PropertyFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    is_public_information: auto
    is_product_type: auto
    type: auto
    internal_name: auto
    missing_main_translation: Optional[bool]
    missing_translations: Optional[bool]

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
            )
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
            ids: list[int] = []

            properties = queryset.select_related("multi_tenant_company").prefetch_related(
                "propertytranslation_set"
            )

            for prop in properties:
                required_languages = set(prop.multi_tenant_company.languages or [])
                translation_languages = {
                    pt.language for pt in prop.propertytranslation_set.all()
                }
                is_missing = not required_languages.issubset(translation_languages)

                if (value and is_missing) or (not value and not is_missing):
                    ids.append(prop.id)

            queryset = queryset.filter(id__in=ids)

        return queryset, Q()


@filter(PropertySelectValue)
class PropertySelectValueFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    property: Optional[PropertyFilter]
    image: Optional[ImageFilter]
    missing_main_translation: Optional[bool]
    missing_translations: Optional[bool]

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
            )
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
            ids: list[int] = []

            values = queryset.select_related("multi_tenant_company").prefetch_related(
                "propertyselectvaluetranslation_set"
            )

            for val in values:
                required_languages = set(val.multi_tenant_company.languages or [])
                translation_languages = {
                    pt.language for pt in val.propertyselectvaluetranslation_set.all()
                }
                is_missing = not required_languages.issubset(translation_languages)

                if (value and is_missing) or (not value and not is_missing):
                    ids.append(val.id)

            queryset = queryset.filter(id__in=ids)

        return queryset, Q()


@filter(PropertySelectValueTranslation)
class PropertySelectValueTranslationFilter:
    id: auto
    value: auto
    propertyselectvalue: Optional[PropertySelectValueFilter]


@filter(ProductProperty)
class ProductPropertyFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    product: Optional[ProductFilter]
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
