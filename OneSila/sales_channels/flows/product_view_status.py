from __future__ import annotations

from typing import Any

from sales_channels.models import RejectedSalesChannelViewAssign, SalesChannelViewAssign
from sales_channels.signals import product_view_status_changed


STATUS_ADDED = "ADDED"
STATUS_REJECT = "REJECT"
STATUS_TODO = "TODO"


def _status_value(*, status: Any) -> str:
    return str(getattr(status, "value", status))


def change_product_view_status_for_assign_object(
    *,
    product,
    sales_channel_view,
    status,
    multi_tenant_company,
    multi_tenant_user=None,
) -> dict[str, int]:
    status_value = _status_value(status=status)
    if status_value not in {STATUS_ADDED, STATUS_REJECT, STATUS_TODO}:
        raise ValueError(f"Unknown product view status: {status_value}")

    assign_filter = {
        "product": product,
        "sales_channel_view": sales_channel_view,
    }
    common_values = {
        **assign_filter,
        "multi_tenant_company": multi_tenant_company,
    }
    user_values = {}
    if multi_tenant_user is not None:
        user_values = {
            "created_by_multi_tenant_user": multi_tenant_user,
            "last_update_by_multi_tenant_user": multi_tenant_user,
        }

    created_count = 0
    deleted_count = 0

    if status_value == STATUS_ADDED:
        deleted_count += RejectedSalesChannelViewAssign.objects.filter(**assign_filter).delete()[0]
        _, created = SalesChannelViewAssign.objects.get_or_create(
            **common_values,
            defaults={
                **user_values,
                "sales_channel": sales_channel_view.sales_channel,
            },
        )
        created_count += int(created)
        result = {"created_count": created_count, "deleted_count": deleted_count}
        product_view_status_changed.send(
            sender=product.__class__,
            instance=product,
            sales_channel_view=sales_channel_view,
            status=status_value,
        )
        return result

    if status_value == STATUS_TODO:
        deleted_count += RejectedSalesChannelViewAssign.objects.filter(**assign_filter).delete()[0]
        deleted_count += SalesChannelViewAssign.objects.filter(**assign_filter).delete()[0]
        result = {"created_count": created_count, "deleted_count": deleted_count}
        product_view_status_changed.send(
            sender=product.__class__,
            instance=product,
            sales_channel_view=sales_channel_view,
            status=status_value,
        )
        return result

    deleted_count += SalesChannelViewAssign.objects.filter(**assign_filter).delete()[0]
    _, created = RejectedSalesChannelViewAssign.objects.get_or_create(
        **common_values,
        defaults=user_values,
    )
    created_count += int(created)
    result = {"created_count": created_count, "deleted_count": deleted_count}
    product_view_status_changed.send(
        sender=product.__class__,
        instance=product,
        sales_channel_view=sales_channel_view,
        status=status_value,
    )
    return result
