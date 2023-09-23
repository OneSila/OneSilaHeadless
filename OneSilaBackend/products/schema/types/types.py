from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation, \
    ProductTranslation, UmbrellaVariation, BundleVariation
from .filters import ProductFilter, BundleProductFilter, UmbrellaProductFilter, \
    ProductVariationFilter, ProductTranslationFilter, UmbrellaVariationFilter, BundleVariationFilter
from .ordering import ProductOrder, BundleProductOrder, UmbrellaProductOrder, \
    ProductVariationOrder, ProductTranslationOrder, UmbrellaVariationOrder, BundleVariationOrder


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(BundleProduct, filters=BundleProductFilter, order=BundleProductOrder, pagination=True, fields="__all__")
class BundleProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(UmbrellaProduct, filters=UmbrellaProductFilter, order=UmbrellaProductOrder, pagination=True, fields="__all__")
class UmbrellaProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductVariation, filters=ProductVariationFilter, order=ProductVariationOrder, pagination=True, fields="__all__")
class ProductVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(UmbrellaVariation, filters=UmbrellaVariationFilter, order=UmbrellaVariationOrder, pagination=True, fields="__all__")
class UmbrellaVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
