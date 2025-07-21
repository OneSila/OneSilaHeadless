from strawberry.exceptions import StrawberryException

from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import CreateMutation, UpdateMutation
from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from properties.models import ProductPropertiesRule, ProductProperty, ProductPropertyTextTranslation, Property
from strawberry_django.mutations.types import UNSET
from django.utils.translation import gettext_lazy as _


class CompleteCreateProductPropertiesRule(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):

        with DjangoOptimizerExtension.disabled():
            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            items = data.get("items")
            product_type = data.get("product_type")
            require_ean_code = data.pop("require_ean_code", False)

            if items == UNSET:
                items = []

            rule = ProductPropertiesRule.objects.create_rule(multi_tenant_company, product_type, require_ean_code, items)
            return rule


class CompleteUpdateProductPropertiesRule(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: ProductPropertiesRule, data: dict[str, Any]):

        with DjangoOptimizerExtension.disabled():
            items = data.pop("items", [])
            require_ean_code = data.pop("require_ean_code", None)

            if require_ean_code is not None:
                if require_ean_code != instance.require_ean_code:
                    instance.require_ean_code = require_ean_code
                    instance.save()

            if items == UNSET:
                items = []

            rule = ProductPropertiesRule.objects.update_rule_items(instance, items)
            return rule


class BulkCreateProductProperties(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info) -> ProductProperty | None:
        with DjangoOptimizerExtension.disabled():
            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            multi_tenant_user = self.get_current_user(info, fail_silently=False)
            extra_kwargs = {
                'multi_tenant_company': multi_tenant_company,
                'created_by_multi_tenant_user': multi_tenant_user,
                'last_update_by_multi_tenant_user': multi_tenant_user,
            }

            input_data = data.get("product_property", {})
            override = data.get("override_if_exists", False)

            product = input_data.get("product")
            property = input_data.get("property")

            if not product or not property:
                raise StrawberryException(_("Missing product or property."))

            product_obj = product.pk
            property_obj = property.pk

            if not product_obj or not property_obj:
                raise StrawberryException(_("Missing product or property."))


            product_id = product_obj.id
            property_id = property_obj.id

            if not product_id or not property_id:
                raise StrawberryException(_("Missing product or property."))

            language_code = data.get("language_code")
            translated_value = data.get("translated_value")

            try:
                obj = ProductProperty.objects.get(product_id=product_id, property_id=property_id)

                if override:

                    # Update scalar values (ignore nulls/unset)
                    for field in [
                        "value_boolean",
                        "value_int",
                        "value_float",
                        "value_date",
                        "value_datetime",
                    ]:
                        if field in input_data and input_data[field] != UNSET:
                            setattr(obj, field, input_data[field])

                    # Handle many-to-many for value_multi_select if provided
                    if "value_multi_select" in input_data:

                        values = []
                        if input_data.get("value_multi_select") != UNSET:
                            for value in input_data["value_multi_select"]:
                                values.append(value.pk.id)

                        obj.value_multi_select.set(values)

                    if "value_select" in input_data and input_data["value_select"] != UNSET:
                        obj.value_select = input_data.get('value_select').pk

                    obj.save()

            except ProductProperty.DoesNotExist:
                create_data = {
                    k: (v.pk if hasattr(v, 'pk') else v)
                    for k, v in input_data.items()
                    if v != UNSET and k != "value_multi_select" and k != "value_select"
                }

                create_data.update(extra_kwargs)
                obj = ProductProperty.objects.create(**create_data)

                # Handle ManyToManyField: value_multi_select
                if "value_multi_select" in input_data and input_data["value_multi_select"] != UNSET:
                    values = [v.pk.id for v in input_data["value_multi_select"]]
                    obj.value_multi_select.set(values)

                # Handle ForeignKey: value_select
                if "value_select" in input_data and input_data["value_select"] != UNSET:
                    obj.value_select = input_data["value_select"].pk
                    obj.save()

            # Handle translations (text / description)
            if language_code and translated_value:
                prop_type = obj.property.type

                try:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=obj,
                        language=language_code
                    )

                    if not override:
                        return obj

                except ProductPropertyTextTranslation.DoesNotExist:
                    translation = ProductPropertyTextTranslation(
                        product_property=obj,
                        language=language_code,
                        **extra_kwargs
                    )

                if prop_type == Property.TYPES.TEXT:
                    translation.value_text = translated_value
                elif prop_type == Property.TYPES.DESCRIPTION:
                    translation.value_description = translated_value

                translation.save()

            return obj


