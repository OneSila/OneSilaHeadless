from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation, \
    ProductTranslation, UmbrellaVariation, BundleVariation


@input(Product, fields="__all__")
class ProductInput:
    pass


@partial(Product, fields="__all__")
class ProductPartialInput(NodeInput):
    pass


@input(BundleProduct, fields="__all__")
class BundleProductInput:
    pass


@partial(BundleProduct, fields="__all__")
class BundleProductPartialInput(NodeInput):
    pass


@input(UmbrellaProduct, fields="__all__")
class UmbrellaProductInput:
    pass


@partial(UmbrellaProduct, fields="__all__")
class UmbrellaProductPartialInput(NodeInput):
    pass


@input(ProductVariation, fields="__all__")
class ProductVariationInput:
    pass


@partial(ProductVariation, fields="__all__")
class ProductVariationPartialInput(NodeInput):
    pass


@input(ProductTranslation, fields="__all__")
class ProductTranslationInput:
    pass


@partial(ProductTranslation, fields="__all__")
class ProductTranslationPartialInput(NodeInput):
    pass


@input(UmbrellaVariation, fields="__all__")
class UmbrellaVariationInput:
    pass


@partial(UmbrellaVariation, fields="__all__")
class UmbrellaVariationPartialInput(NodeInput):
    pass


@input(BundleVariation, fields="__all__")
class BundleVariationInput:
    pass


@partial(BundleVariation, fields="__all__")
class BundleVariationPartialInput(NodeInput):
    pass
