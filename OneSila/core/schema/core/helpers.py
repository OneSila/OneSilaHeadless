from strawberry.types import Info
from strawberry_django.auth.utils import get_current_user, aget_current_user

from asgiref.sync import sync_to_async


def get_multi_tenant_company(info: Info, fail_silently=True):
    user = get_current_user(info)

    multi_tenant_company = user.multi_tenant_company

    if not fail_silently and not multi_tenant_company:
        raise ValueError("User is not assigned to a multi tenant company.")

    return multi_tenant_company
