from typing import Any

from strawberry import Info

from strawberry_django.optimizer import DjangoOptimizerExtension

from core.schema.core.mutations import CreateMutation
from products.models import AliasProduct
from translations.schema.mutations import TranslatableCreateMutation


class AliasProductCreateMutation(TranslatableCreateMutation):
    def __init__(self, *args, extensions, translation_model, translation_field, translation_model_to_model_field, **kwargs):
        super().__init__(
            *args,
            extensions=extensions,
            translation_model=translation_model,
            translation_field=translation_field,
            translation_model_to_model_field=translation_model_to_model_field,
            **kwargs
        )

    def create(self, data: dict[str, Any], *, info: Info):
        instance = super().create(data=data, info=info)

        if instance.is_alias() and instance.alias_parent_product:
            AliasProduct.objects.copy_from_parent(
                instance,
                copy_images=data.get("alias_copy_images", False),
                copy_properties=data.get("alias_copy_product_properties", False),
                copy_content=data.get("alias_copy_content", True),
            )

        instance.refresh_from_db()
        return instance



