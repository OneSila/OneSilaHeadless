from strawberry_django import auth, field
import secrets
import uuid

from core.models import MultiTenantUser, DashboardSection, DashboardCard
from core.schema.core.helpers import get_multi_tenant_company, get_current_user
from core.schema.multi_tenant.types.types import (
    MultiTenantUserType,
    MultiTenantCompanyType,
    HasDemoDataType,
    MinimalMultiTenantUserType,
    UserCredentialsType,
    DashboardSectionType,
    DashboardCardType,
)
from core.schema.core.queries import connection, DjangoListConnection, \
    type, field, Info, List, anonymous_field


def my_multi_tenant_company_resolver(info: Info) -> MultiTenantCompanyType:
    multi_tenant_company = get_multi_tenant_company(info)
    return multi_tenant_company


def users_resolver(info: Info) -> List[MultiTenantUserType]:
    multi_tenant_company = get_multi_tenant_company(info)
    users = multi_tenant_company.multitenantuser_set.all()
    return users


def has_demo_data(info: Info) -> HasDemoDataType:
    multi_tenant_company = get_multi_tenant_company(info)
    return HasDemoDataType(has_demo_data=multi_tenant_company.demodatarelation_set.all().exists())


def generate_user_credentials_resolver(info: Info, identifier: str | None = None) -> UserCredentialsType:

    def generate_username() -> str:
        if identifier:
            base = f"shopifyfakeuser_{uuid.uuid4().hex[:8]}_{identifier}"
        else:
            base = f"shopifyfakeuser_{uuid.uuid4().hex[:8]}"

        return f"{base}@onesila.app"

    username = generate_username()
    while MultiTenantUser.objects.filter(username=username).exists():
        username = generate_username()

    password = secrets.token_urlsafe(16)

    return UserCredentialsType(username=username, password=password)


def dashboard_sections_resolver(info: Info):
    user = get_current_user(info)
    if user is None:
        return DashboardSection.objects.none()
    return (
        DashboardSection.objects.filter(
            multi_tenant_company=user.multi_tenant_company,
            user=user,
        )
        .select_related("user")
        .prefetch_related("cards__user", "cards__section")
    )


def dashboard_cards_resolver(info: Info):
    user = get_current_user(info)
    if user is None:
        return DashboardCard.objects.none()
    return DashboardCard.objects.filter(
        multi_tenant_company=user.multi_tenant_company,
        user=user,
    ).select_related("user", "section")


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()
    my_multi_tenant_company: MultiTenantCompanyType = field(resolver=my_multi_tenant_company_resolver)
    users: DjangoListConnection[MinimalMultiTenantUserType] = connection()
    has_demo_data: HasDemoDataType = anonymous_field(resolver=has_demo_data)
    dashboard_sections: DjangoListConnection[DashboardSectionType] = connection()
    dashboard_cards: DjangoListConnection[DashboardCardType] = connection()

    generate_user_credentials: UserCredentialsType = anonymous_field(
        resolver=generate_user_credentials_resolver
    )
