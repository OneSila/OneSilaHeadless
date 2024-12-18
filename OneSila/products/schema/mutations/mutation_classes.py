from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation
from products.models import SupplierPrice
from units.models import Unit
from translations.schema.mutations import TranslatableCreateMutation


class CreateSupplierProductMutation(TranslatableCreateMutation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, data: dict[str, Any], *, info: Info):
        unit = data.pop('unit', None)
        quantity = data.pop('quantity', None)
        unit_price = data.pop('unit_price', None)
        supplier_product = super().create(data=data, info=info)

        unit_obj = Unit.objects.get(pk=unit.pk.id)
        SupplierPrice.objects.create(
            supplier_product=supplier_product,
            unit=unit_obj,
            quantity=quantity,
            unit_price=unit_price,
            multi_tenant_company=supplier_product.multi_tenant_company,
        )

        supplier_product.refresh_from_db()

        return supplier_product
