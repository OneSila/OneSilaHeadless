from django.db import models
from strawberry_django import order_field, Ordering
from strawberry_django.auth.utils import get_current_user

from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from properties.models import Property, PropertySelectValue, \
    ProductProperty, PropertyTranslation, ProductPropertyTextTranslation, PropertySelectValueTranslation, ProductPropertiesRuleItem, ProductPropertiesRule


@order(Property)
class PropertyOrder:
    id: auto
    type: auto
    created_at: auto


@order(PropertySelectValue)
class PropertySelectValueOrder:
    id: auto
    created_at: auto

    @order_field
    def usage_count(
        self,
        *,
        queryset,
        info,
        value: Ordering,
        prefix: str,
    ) -> tuple[models.QuerySet, list[str]]:
        user = get_current_user(info)
        if user is None:
            return queryset, [value.resolve(f"{prefix}id")]

        queryset = (
            queryset.with_usage_count(multi_tenant_company_id=user.multi_tenant_company_id)
            .with_translated_value()
        )
        return queryset, [
            value.resolve(f"{prefix}usage_count"),
            f"{prefix}translated_value",
            f"{prefix}id",
        ]


@order(PropertySelectValueTranslation)
class PropertySelectValueTranslationOrder:
    id: auto
    value: auto


@order(ProductProperty)
class ProductPropertyOrder:
    id: auto
    value_select: auto
    value_multi_select: auto
    created_at: auto


@order(PropertyTranslation)
class PropertyTranslationOrder:
    id: auto


@order(ProductPropertyTextTranslation)
class ProductPropertyTextTranslationOrder:
    id: auto


@order(ProductPropertiesRule)
class ProductPropertiesRuleOrder:
    id: auto
    product_type: auto
    created_at: auto


@order(ProductPropertiesRuleItem)
class ProductPropertiesRuleItemOrder:
    sort_order: auto
    created_at: auto
