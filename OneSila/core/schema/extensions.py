from strawberry.types.info import Info
from strawberry_django.utils.typing import UserType
from strawberry_django.resolvers import django_resolver
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.permissions import DjangoPermissionExtension, \
    _desc

from core.schema.exceptions import NotAuthenticatedError, \
    MultiTentantCompanyMissingError

from typing import Callable, Optional, ClassVar, Any


class HasMultiTenantCompany(DjangoPermissionExtension):
    """Mark a field as only resolvable by superuser users."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User has no `multi_tenant_company` set."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str] = _desc(
        "Can only be resolved by users where a `multi_tenant_company` is set.",
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
            if not user.multi_tenant_company:
                raise MultiTentantCompanyMissingError()
        except AttributeError:
            raise MultiTentantCompanyMissingError()

        return resolver()


class IsAuthenticated(DjangoPermissionExtension):
    """Mark a field as only resolvable by superuser users."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User is not authenticated."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str] = _desc(
        "Can only be resolved by users whom are authenticated, and have an active account.",
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
            if not user.is_authenticated or not user.is_active:
                raise NotAuthenticatedError("User is not authenticated")
        except AttributeError:
            raise NotAuthenticatedError("User is not authenticated")

        return resolver()


default_extensions = [HasMultiTenantCompany(), IsAuthenticated()]
