import strawberry

from core.schema.core.types.types import type, relay, lazy, Annotated, field, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.core.helpers import get_current_user

from core.schema.multi_tenant.types.ordering import (
    MultiTenantUserOrder,
    DashboardSectionOrder,
    DashboardCardOrder,
)
from core.schema.multi_tenant.types.filters import (
    MultiTenantUserFilter,
    DashboardSectionFilter,
    DashboardCardFilter,
)
from core.models.multi_tenant import (
    MultiTenantCompany,
    MultiTenantUser,
    MultiTenantUserLoginToken,
    DashboardSection,
    DashboardCard,
)

from strawberry_django.fields.types import DjangoImageType
from typing import List, TYPE_CHECKING

from core.typing import TimezoneType

if TYPE_CHECKING:
    from core.schema.languages.types.types import LanguageType


@type(MultiTenantUser, filters=MultiTenantUserFilter, order=MultiTenantUserOrder, pagination=True, fields=['multi_tenant_company', 'id', 'first_name', 'last_name', 'email', 'is_active'])
class MinimalMultiTenantUserType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: Annotated['MultiTenantCompanyType', lazy("core.schema.multi_tenant.types.types")] | None

    @field()
    def full_name(self, info) -> str | None:
        return self.full_name


@type(MultiTenantUser, filters=MultiTenantUserFilter, order=MultiTenantUserOrder, pagination=True, fields='__all__')
class MultiTenantUserType(relay.Node):
    avatar_resized: DjangoImageType | None
    avatar_resized_full_url: str | None
    language_detail: Annotated['LanguageType', lazy("core.schema.languages.types.types")]
    timezone_detail: TimezoneType
    multi_tenant_company: Annotated['MultiTenantCompanyType', lazy("core.schema.multi_tenant.types.types")] | None

    @field()
    def full_name(self, info) -> str | None:
        return self.full_name


@type(MultiTenantCompany, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    multitenantuser_set: List[MultiTenantUserType]
    language_detail: Annotated['LanguageType', lazy("core.schema.languages.types.types")]

    @field()
    def full_address(self, info) -> str:
        return self.full_address

    @field()
    def has_amazon_integration(self, info) -> bool:
        from sales_channels.integrations.amazon.models.sales_channels import AmazonSalesChannel
        return AmazonSalesChannel.objects.filter(multi_tenant_company=self, active=True).exists()

    @field()
    def has_ebay_integration(self, info) -> bool:
        from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel
        return EbaySalesChannel.objects.filter(multi_tenant_company=self, active=True).exists()

    @field()
    def has_shein_integration(self, info) -> bool:
        from sales_channels.integrations.shein.models.sales_channels import SheinSalesChannel
        return SheinSalesChannel.objects.filter(multi_tenant_company=self, active=True).exists()


@type(MultiTenantUserLoginToken, exclude=['token'])
class MultiTenantUserLoginTokenType(relay.Node):
    pass


@strawberry.type
class HasDemoDataType:
    has_demo_data: bool


@strawberry_type
class UserCredentialsType:
    username: str
    password: str


@type(DashboardSection, filters=DashboardSectionFilter, order=DashboardSectionOrder, pagination=True, fields='__all__')
class DashboardSectionType(relay.Node, GetQuerysetMultiTenantMixin):
    user: Annotated['MultiTenantUserType', lazy("core.schema.multi_tenant.types.types")]
    cards: List[Annotated['DashboardCardType', lazy("core.schema.multi_tenant.types.types")]]


@type(DashboardCard, filters=DashboardCardFilter, order=DashboardCardOrder, pagination=True, fields='__all__')
class DashboardCardType(relay.Node, GetQuerysetMultiTenantMixin):
    user: Annotated['MultiTenantUserType', lazy("core.schema.multi_tenant.types.types")]
    section: Annotated['DashboardSectionType', lazy("core.schema.multi_tenant.types.types")]
