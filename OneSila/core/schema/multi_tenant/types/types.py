from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay, auto, lazy, Annotated
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from core.schema.multi_tenant.types.ordering import MultiTenantUserOrder
from core.schema.multi_tenant.types.filters import MultiTenantUserFilter
from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser, MultiTenantUserLoginToken

from strawberry_django.fields.types import DjangoImageType
from typing import List, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from core.schema.languages.types.types import LanguageType


@type(MultiTenantUser, filters=MultiTenantUserOrder, order=MultiTenantUserFilter, pagination=True, fields='__all__')
class MultiTenantUserType(relay.Node):
    avatar_resized: DjangoImageType | None
    avatar_resized_full_url: str | None
    language_detail: Annotated['LanguageType', lazy("core.schema.languages.types.types")]
    multi_tenant_company: Annotated['MultiTenantCompanyType', lazy("core.schema.multi_tenant.types.types")]


@type(MultiTenantCompany, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    multitenantuser_set: List[MultiTenantUserType]
    language_detail: Annotated['LanguageType', lazy("core.schema.languages.types.types")]


@type(MultiTenantUserLoginToken, exclude=['token'])
class MultiTenantUserLoginTokenType(relay.Node):
    pass
