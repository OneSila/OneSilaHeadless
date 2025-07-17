from typing import Optional

from django.db import models
from strawberry_django import order_field, Ordering

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from products.models import (
    Product,
    BundleProduct,
    ConfigurableProduct,
    SimpleProduct,
    ProductTranslation,
    ConfigurableVariation,
    BundleVariation,
    AliasProduct,
    ProductTranslationBulletPoint,
)


@order(Product)
class ProductOrder:
    id: auto
    sku: auto
    active: auto
    created_at: auto
    updated_at: auto

    @order_field
    def name(
        self,
        queryset,
        info,
        value: Ordering,
        prefix: str,
    ) -> tuple[models.QuerySet, list[str]]:
        multi_tenant_company = get_multi_tenant_company(info)
        queryset = queryset.with_translated_name(multi_tenant_company.language)
        return queryset, [value.resolve(f"{prefix}translated_name")]


@order(BundleProduct)
class BundleProductOrder:
    id: auto
    sku: auto


@order(ConfigurableProduct)
class ConfigurableProductOrder:
    id: auto
    sku: auto


@order(AliasProduct)
class AliasProductOrder:
    id: auto
    sku: auto


@order(SimpleProduct)
class SimpleProductOrder:
    id: auto
    sku: auto


@order(ProductTranslation)
class ProductTranslationOrder:
    id: auto


@order(ConfigurableVariation)
class ConfigurableVariationOrder:
    id: auto


@order(BundleVariation)
class BundleVariationOrder:
    id: auto


@order(ProductTranslationBulletPoint)
class ProductTranslationBulletPointOrder:
    id: auto
    sort_order: auto
