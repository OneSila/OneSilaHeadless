from strawberry.types import Info
from strawberry_django.auth.utils import get_current_user


def get_multi_tenant_company(info: Info, fail_silently=True):
    user = get_current_user(info)

    multi_tenant_company = user.multi_tenant_company

    if not fail_silently and not multi_tenant_company:
        raise ValueError("multi_tenant_company is missing from mutation.")

    return multi_tenant_company
