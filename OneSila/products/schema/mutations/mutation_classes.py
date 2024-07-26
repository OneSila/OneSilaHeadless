from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation
from products.models import SupplierPrices
from units.models import Unit


# class CreateProductMutation(CreateMutation):
#     def create(self, data: dict[str, Any], *, info: Info):
#         from products.models import ProductTranslation

#         with DjangoOptimizerExtension.disabled():

#             multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
#             language = multi_tenant_company.language

#             data['multi_tenant_company'] = multi_tenant_company

#             product = super().create(data=data, info=info)

#             ProductTranslation.objects.create(
#                 product=product,
#                 language=language,
#                 name=data['name'],
#                 multi_tenant_company=multi_tenant_company,
#             )
#             product.refresh_from_db()
#             return product


class CreateSupplierProductMutation(CreateProductMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        unit = data.pop('unit', None)
        quantity = data.pop('quantity', None)
        unit_price = data.pop('unit_price', None)
        supplier_product = super().create(data=data, info=info)

        unit_obj = Unit.objects.get(pk=unit.pk.id)
        SupplierPrices.objects.create(
            supplier_product=supplier_product,
            unit=unit_obj,
            quantity=quantity,
            unit_price=unit_price,
            multi_tenant_company=supplier_product.multi_tenant_company,
        )

        supplier_product.refresh_from_db()

        return supplier_product
