from typing import Any
from strawberry import Info
from products.product_types import ALIAS
from translations.schema.mutations import TranslatableCreateMutation
from media.models import MediaProductThrough
from properties.models import ProductProperty, Property, ProductPropertyTextTranslation


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

        if instance.type == ALIAS and instance.alias_parent_product:
            parent = instance.alias_parent_product
            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)

            if data.get("alias_copy_images", False):
                parent_images = parent.mediaproductthrough_set.all()
                MediaProductThrough.objects.bulk_create([
                    MediaProductThrough(
                        media=img.media,
                        product=instance,
                        sort_order=img.sort_order,
                        is_main_image=img.is_main_image,
                        multi_tenant_company=multi_tenant_company
                    ) for img in parent_images
                ])

            if data.get("alias_copy_product_properties", False):
                parent_props = ProductProperty.objects.filter(product=parent).select_related('property')

                for pp in parent_props:
                    # Create each ProductProperty manually
                    new_pp = ProductProperty.objects.create(
                        product=instance,
                        property=pp.property,
                        value_boolean=pp.value_boolean,
                        value_int=pp.value_int,
                        value_float=pp.value_float,
                        value_date=pp.value_date,
                        value_datetime=pp.value_datetime,
                        value_select=pp.value_select,
                        multi_tenant_company=multi_tenant_company
                    )

                    # If the property is translatable, clone its text translations
                    if pp.property.type in Property.TYPES.TRANSLATED:
                        text_translations = ProductPropertyTextTranslation.objects.filter(product_property=pp)
                        for trans in text_translations:
                            ProductPropertyTextTranslation.objects.create(
                                product_property=new_pp,
                                language=trans.language,
                                value_text=trans.value_text,
                                value_description=trans.value_description,
                                multi_tenant_company=multi_tenant_company
                            )

        instance.refresh_from_db()
        return instance