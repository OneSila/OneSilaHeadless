from enum import Enum
from typing import Annotated

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from strawberry import Info, lazy

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import List
from core.schema.core.types.input import strawberry_input
from core.schema.core.types.types import strawberry_type
from products.models import Product
from sales_channels.flows.product_view_status import change_product_view_status_for_assign_object
from sales_channels.models import SalesChannelView
from sales_channels.schema.types.input import SalesChannelViewPartialInput


class ProductViewStatus(Enum):
    REJECT = "REJECT"
    TODO = "TODO"
    ADDED = "ADDED"


@strawberry_input
class SalesChannelViewAssignObjectInput:
    product: Annotated['ProductPartialInput', lazy("products.schema.types.input")]
    view: SalesChannelViewPartialInput


@strawberry_input
class ProductViewStatusChangeInput:
    status: ProductViewStatus
    assign_object: SalesChannelViewAssignObjectInput


@strawberry_type
class ProductViewStatusChangeResult:
    status: ProductViewStatus
    products_count: int
    views_count: int
    created_count: int
    deleted_count: int


@strawberry_type
class ProductViewStatusBulkChangeResult:
    changes_count: int
    created_count: int
    deleted_count: int


def _get_node_id(*, node_input, field_name: str) -> int:
    global_id = getattr(node_input, "id", None)
    if not global_id:
        raise ValidationError(_("%(field)s is required.") % {"field": field_name})

    return global_id.node_id


def _resolve_assign_object(*, assign_object: SalesChannelViewAssignObjectInput, multi_tenant_company):
    product_id = _get_node_id(node_input=assign_object.product, field_name="product")
    view_id = _get_node_id(node_input=assign_object.view, field_name="view")

    product = Product.objects.filter(
        id=product_id,
        multi_tenant_company=multi_tenant_company,
    ).first()
    if product is None:
        raise ValidationError(_("Unknown product."))

    view = SalesChannelView.objects.filter(
        id=view_id,
        multi_tenant_company=multi_tenant_company,
    ).select_related("sales_channel").first()
    if view is None:
        raise ValidationError(_("Unknown sales channel view."))

    return product, view


@transaction.atomic
def resolve_change_product_view_status(
    *,
    status: ProductViewStatus,
    assign_object: SalesChannelViewAssignObjectInput,
    info: Info,
) -> ProductViewStatusChangeResult:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    multi_tenant_user = GetCurrentUserMixin.get_current_user(info, fail_silently=True)
    product, view = _resolve_assign_object(
        assign_object=assign_object,
        multi_tenant_company=multi_tenant_company,
    )
    result = change_product_view_status_for_assign_object(
        product=product,
        sales_channel_view=view,
        status=status,
        multi_tenant_company=multi_tenant_company,
        multi_tenant_user=multi_tenant_user,
    )
    return ProductViewStatusChangeResult(
        status=status,
        products_count=1,
        views_count=1,
        created_count=result["created_count"],
        deleted_count=result["deleted_count"],
    )


@transaction.atomic
def resolve_change_product_views_status(
    *,
    changes: List[ProductViewStatusChangeInput],
    info: Info,
) -> ProductViewStatusBulkChangeResult:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    multi_tenant_user = GetCurrentUserMixin.get_current_user(info, fail_silently=True)
    created_count = 0
    deleted_count = 0

    for change in changes:
        product, view = _resolve_assign_object(
            assign_object=change.assign_object,
            multi_tenant_company=multi_tenant_company,
        )
        result = change_product_view_status_for_assign_object(
            product=product,
            sales_channel_view=view,
            status=change.status,
            multi_tenant_company=multi_tenant_company,
            multi_tenant_user=multi_tenant_user,
        )
        created_count += result["created_count"]
        deleted_count += result["deleted_count"]

    return ProductViewStatusBulkChangeResult(
        changes_count=len(changes),
        created_count=created_count,
        deleted_count=deleted_count,
    )
