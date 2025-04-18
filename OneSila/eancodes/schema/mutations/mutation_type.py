from typing import Optional
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from core.schema.core.mutations import create, update, delete, type, List
from .fields import generate_eancodes, assign_ean_code, release_ean_code
from ..types.types import EanCodeType
from ..types.input import EanCodeInput, EanCodePartialInput, BulkAssignEancodesInput
from strawberry import Info
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
import strawberry_django


@type(name="Mutation")
class EanCodesMutation:
    create_ean_code: EanCodeType = create(EanCodeInput)
    create_ean_codes: List[EanCodeType] = create(EanCodeInput)
    update_ean_code: EanCodeType = update(EanCodePartialInput)
    delete_ean_code: EanCodeType = delete()
    delete_ean_codes: List[EanCodeType] = delete(is_bulk=True)

    generate_ean_codes: Optional[EanCodeType] = generate_eancodes()
    assign_ean_code: EanCodeType = assign_ean_code()
    release_ean_code: EanCodeType = release_ean_code()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def assign_ean_codes(self, instance: BulkAssignEancodesInput, info: Info) -> List[EanCodeType]:
        from products.models import Product
        from eancodes.models import EanCode

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        product_ids = [p.id.node_id for p in instance.products if p]

        if not product_ids:
            raise IntegrityError(_("Please provide at least one product."))

        products = Product.objects.filter(id__in=product_ids, multi_tenant_company=multi_tenant_company)
        ean_codes = []
        for product in products:

            if product.ean_code:
                continue

            to_assign = EanCode.objects.filter_multi_tenant(multi_tenant_company=multi_tenant_company).filter(
                internal=True, already_used=False, product__isnull=True).order_by('ean_code').first()

            if to_assign is None:
                break

            to_assign.product = product
            to_assign.save()

            ean_codes.append(to_assign)

        return list(ean_codes)