from core.schema.core.mutations import default_extensions, UpdateMutation
import strawberry_django
from strawberry_django.resolvers import django_resolver
from core.schema.core.mutations import type
from django.db import transaction
from django.core.exceptions import ValidationError
from core.schema.core.mutations import Info, Any, models
from core.schema.core.helpers import get_multi_tenant_company
from products_inspector.models import Inspector
from products_inspector.schema.types.input import InspectorPartialInput, BulkRefreshInspectorInput
from products_inspector.schema.types.types import InspectorType
from core.schema.core.mixins import GetCurrentUserMixin


class RefreshInspectorMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: Inspector, data: dict[str, Any]):
        instance.inspect_product()
        instance.refresh_from_db()
        return instance


def refresh_inspector():
    extensions = default_extensions
    return RefreshInspectorMutation(InspectorPartialInput, extensions=extensions)


@type(name="Mutation")
class ProductsInspectorMutation:
    refresh_inspector: InspectorType = refresh_inspector()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def bulk_refresh_inspector(self, *, instance: BulkRefreshInspectorInput, info: Info) -> bool:
        from products_inspector.tasks import products_inspector__tasks__bulk_refresh_inspector

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        product_ids = [product.id.node_id for product in instance.products or []]
        if not product_ids:
            raise ValidationError("Products are required.")

        products_inspector__tasks__bulk_refresh_inspector(
            multi_tenant_company_id=multi_tenant_company.id,
            product_ids=product_ids,
        )
        return True
