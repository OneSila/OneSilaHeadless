from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from properties.models import Property, PropertyTranslation, \
    PropertySelectValue, ProductProperty, ProductPropertyTextTranslation, PropertySelectValueTranslation


@input(Property, fields="__all__")
class PropertyInput:
    name: str


@partial(Property, fields="__all__")
class PropertyPartialInput(NodeInput):
    pass


@input(PropertyTranslation, fields="__all__")
class PropertyTranslationInput:
    pass


@partial(PropertyTranslation, fields="__all__")
class PropertyTranslationPartialInput(NodeInput):
    pass


@input(PropertySelectValue, fields="__all__")
class PropertySelectValueInput:
    value: str


@partial(PropertySelectValue, fields="__all__")
class PropertySelectValuePartialInput(NodeInput):
    pass

@input(PropertySelectValueTranslation, fields="__all__")
class PropertySelectValueTranslationInput:
    pass


@partial(PropertySelectValueTranslation, fields="__all__")
class PropertySelectValueTranslationPartialInput(NodeInput):
    pass

@input(ProductProperty, fields="__all__")
class ProductPropertyInput:
    pass


@partial(ProductProperty, fields="__all__")
class ProductPropertyPartialInput(NodeInput):
    pass

@input(ProductPropertyTextTranslation, fields="__all__")
class ProductPropertyTextTranslationInput:
    pass


@partial(ProductPropertyTextTranslation, fields="__all__")
class ProductPropertyTextTranslationPartialInput(NodeInput):
    pass