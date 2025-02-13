from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import CreateMutation, UpdateMutation
from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from properties.models import ProductPropertiesRule
from strawberry_django.mutations.types import UNSET


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
