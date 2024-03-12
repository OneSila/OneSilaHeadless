from strawberry.relay.utils import to_base64
from strawberry_django.relay import resolve_model_id

from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field

from typing import List, Optional

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation, \
    ProductTranslation, UmbrellaVariation, BundleVariation
from taxes.schema.types.types import TaxType
from .filters import ProductFilter, BundleProductFilter, UmbrellaProductFilter, \
    ProductVariationFilter, ProductTranslationFilter, UmbrellaVariationFilter, BundleVariationFilter
from .ordering import ProductOrder, BundleProductOrder, UmbrellaProductOrder, \
    ProductVariationOrder, ProductTranslationOrder, UmbrellaVariationOrder, BundleVariationOrder


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    tax_rate: TaxType

    @field()
    def proxy_id(self, info) -> str:
        if self.is_variation():
            graphql_type = ProductVariationType
        elif self.is_bundle():
            graphql_type = BundleProductType
        elif self.is_umbrella():
            graphql_type = UmbrellaProductType
        else:
            graphql_type = ProductType

        return to_base64(graphql_type, self.pk)

    # @TODO: Improve that in the future to get the current language or something like this rn it need discussion because translations languages are different
    @field()
    def name(self, info) -> str | None:
        translation = self.translations.first()
        return None if translation is None else translation.name


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
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    umbrella: Optional[ProductType]
    variation: Optional[ProductType]
