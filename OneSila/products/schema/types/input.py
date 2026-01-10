from typing import List, Optional
from enum import Enum

import strawberry

from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from products.models import (
    Product,
    BundleProduct,
    ConfigurableProduct,
    SimpleProduct,
    ProductTranslation,
    ConfigurableVariation,
    BundleVariation,
    ProductTranslationBulletPoint,
)
from properties.schema.types.input import (
    ProductPropertiesRulePartialInput,
    PropertySelectValuePartialInput,
)
from sales_channels.schema.types.input import SalesChannelPartialInput


class ContentField(Enum):
    DESCRIPTION = "description"
    SHORT_DESCRIPTION = "short_description"
    SUBTITLE = "subtitle"
    NAME = "name"
    BULLET_POINTS = "bullet_points"
    URL_KEY = "url_key"


@input(Product, fields="__all__")
class ProductInput:
    name: str
    alias_copy_images: bool
    alias_copy_product_properties: bool
    alias_copy_content: bool = True


@partial(Product, fields="__all__")
class ProductPartialInput(NodeInput):
    pass


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


@input(ProductTranslationBulletPoint, fields="__all__")
class ProductTranslationBulletPointInput:
    pass


@partial(ProductTranslationBulletPoint, fields="__all__")
class ProductTranslationBulletPointPartialInput(NodeInput):
    pass


@strawberry_input
class ProductTranslationBulkImportInput:
    channel_source: Optional[SalesChannelPartialInput] = None
    channel_target: Optional[SalesChannelPartialInput] = None
    language: Optional[str] = None
    override: Optional[bool] = False
    all_languages: Optional[bool] = False
    fields: List[ContentField]
    products: List[ProductPartialInput]

