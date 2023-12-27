from strawberry.types.info import Info
from strawberry_django.utils.typing import UserType
from strawberry_django.resolvers import django_resolver
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.permissions import DjangoPermissionExtension, \
    _desc

from core.schema.multi_tenant.exceptions import NotMultiTenantCompanyOwner

from typing import Callable, Optional, ClassVar, Any


class IsMultiTenantCompanyOwner(DjangoPermissionExtension):
    """Mark a field as only resolvable by superuser users."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User is not the company owner."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str] = _desc(
        "Can only be used by users who have `is_multi_tenant_company_owner` set to True.",
    )

    @django_resolver(qs_hook=None)
    def resolve_for_user(
        self,
        resolver: Callable,
        user: Optional[UserType],
        *,
        info: Info,
        source: Any,
    ):
        try:
            if not user.is_multi_tenant_company_owner:
                raise NotMultiTenantCompanyOwner(self.DEFAULT_ERROR_MESSAGE)
        except AttributeError:
            raise NotMultiTenantCompanyOwner(self.DEFAULT_ERROR_MESSAGE)

        return resolver()
