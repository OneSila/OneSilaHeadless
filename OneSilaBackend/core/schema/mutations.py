from django.db import models
from django.core.exceptions import PermissionDenied

import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from strawberry_django.mutations.fields import DjangoCreateMutation, \
    DjangoUpdateMutation, DjangoDeleteMutation
from typing import TYPE_CHECKING, Any, Iterable, Union
from strawberry.types import Info
from strawberry import type
from typing import List

from .decorators import multi_tenant_owner_protection
from .mixins import GetMultiTenantCompanyMixin


class CreateMutation(GetMultiTenantCompanyMixin, DjangoCreateMutation):
    """
    Every create needs to include the company a user is assigned to.
    """

    def create(self, data: dict[str, Any], *, info: Info):
        data['multi_tenant_company'] = self.get_multi_tenant_company(info)
        return super().create(data=data, info=info)


class UpdateMutation(GetMultiTenantCompanyMixin, DjangoUpdateMutation):
    """
    You can only update if the object is owned by the user company
    """
    @multi_tenant_owner_protection()
    def update(self, info: Info, instance: models.Model | Iterable[models.Model], data: dict[str, Any],):
        return super().update(info=info, instance=instance, data=data)


class DeleteMutation(GetMultiTenantCompanyMixin, DjangoDeleteMutation):
    """
    You can only delete if the object is owned by the comnpany represented
    """
    @multi_tenant_owner_protection()
    def delete(self, info: Info, instance: models.Model | Iterable[models.Model]):
        return super().delete(info=info, instance=instance)


def create(type):
    extensions = [IsAuthenticated()]
    return CreateMutation(type, extensions=extensions)


def update(type):
    extensions = [IsAuthenticated()]
    return UpdateMutation(type, extensions=extensions)


def delete():
    extensions = [IsAuthenticated()]
    return DeleteMutation(strawberry_django.NodeInput, extensions=extensions)
