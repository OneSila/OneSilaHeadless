from django.db import models
from django.core.exceptions import PermissionDenied

import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from strawberry_django.mutations.fields import DjangoCreateMutation, \
    DjangoUpdateMutation, DjangoDeleteMutation
from typing import TYPE_CHECKING, Any, Iterable, Union
from strawberry.types import Info
from strawberry import type, field
from typing import List

from .decorators import multi_tenant_owner_protection
from .mixins import GetMultiTenantCompanyMixin, GetCurrentUserMixin
from .extensions import default_extensions
from ...signals import mutation_update, mutation_create


class CreateMutation(GetMultiTenantCompanyMixin, GetCurrentUserMixin, DjangoCreateMutation):
    """
    Every create needs to include the company a user is assigned to.
    """

    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
        multi_tenant_user = self.get_current_user(info, fail_silently=False)
        data['multi_tenant_company'] = multi_tenant_company
        data['created_by_multi_tenant_user'] = multi_tenant_user
        data['last_update_by_multi_tenant_user'] = multi_tenant_user
        created_instance = super().create(data=data, info=info)
        mutation_create.send(sender=created_instance.__class__, instance=created_instance)
        return created_instance


class UpdateMutation(GetMultiTenantCompanyMixin, GetCurrentUserMixin, DjangoUpdateMutation):
    """
    You can only update if the object is owned by the user company
    """
    @multi_tenant_owner_protection()
    def update(self, info: Info, instance: models.Model | Iterable[models.Model], data: dict[str, Any],):
        multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
        multi_tenant_user = self.get_current_user(info, fail_silently=False)
        data['multi_tenant_company'] = multi_tenant_company
        data['last_update_by_multi_tenant_user'] = multi_tenant_user
        updated_instance = super().update(info=info, instance=instance, data=data)
        mutation_update.send(sender=updated_instance.__class__, instance=updated_instance)
        return updated_instance


class DeleteMutation(GetMultiTenantCompanyMixin, DjangoDeleteMutation):
    """
    You can only delete if the object is owned by the comnpany represented
    """
    @multi_tenant_owner_protection()
    def delete(self, info: Info, instance: models.Model | Iterable[models.Model]):
        return super().delete(info=info, instance=instance)


def create(input_type):
    extensions = default_extensions
    return CreateMutation(input_type, extensions=extensions)


def update(input_type):
    extensions = default_extensions
    return UpdateMutation(input_type, extensions=extensions)


def delete():
    extensions = default_extensions
    return DeleteMutation(strawberry_django.NodeInput, extensions=extensions)
