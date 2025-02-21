from decimal import Decimal
from typing import List, Optional
from core.schema.core.types.input import NodeInput, input, partial
from core.schema.core.types.types import Annotated, lazy

from products.models import Product, BundleProduct, ConfigurableProduct, SimpleProduct, \
    ProductTranslation, ConfigurableVariation, BundleVariation

@input(Product, fields="__all__")
class ProductInput:
    name: str


@partial(Product, fields="__all__")
class ProductPartialInput(NodeInput):
    base_products: Optional[List[Annotated['ProductPartialInput', lazy("products.schema.types.input")]]]


@input(BundleProduct, fields="__all__")
class BundleProductInput:
    pass


@partial(BundleProduct, fields="__all__")
class BundleProductPartialInput(NodeInput):
    pass


@input(ConfigurableProduct, fields="__all__")
class ConfigurableProductInput:
    pass


@partial(ConfigurableProduct, fields="__all__")
class ConfigurableProductPartialInput(NodeInput):
    pass


@input(SimpleProduct, fields="__all__")
class SimpleProductInput:
    pass


@partial(SimpleProduct, fields="__all__")
class SimpleProductPartialInput(NodeInput):
    pass


@input(ProductTranslation, fields="__all__")
class ProductTranslationInput:
    pass


@partial(ProductTranslation, fields="__all__")
class ProductTranslationPartialInput(NodeInput):
    pass


@input(ConfigurableVariation, fields="__all__")
class ConfigurableVariationInput:
    pass


@partial(ConfigurableVariation, fields="__all__")
class ConfigurableVariationPartialInput(NodeInput):
    pass


@input(BundleVariation, fields="__all__")
class BundleVariationInput:
    pass


@partial(BundleVariation, fields="__all__")
class BundleVariationPartialInput(NodeInput):
    pass