from django.db import models
from django.core.exceptions import PermissionDenied
from django_shared_multi_tenant.schema import StrawberryMultitenantMixin

import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from strawberry_django.mutations.fields import DjangoCreateMutation, \
    DjangoUpdateMutation, DjangoDeleteMutation
from typing import TYPE_CHECKING, Any, Iterable, Union
from strawberry.types import Info

from functools import wraps


def multi_tenant_owner_protection():
    '''
    Protect data ownership by verifying both:
    - data doesnt contain an override for multi_tenant_company
    - instance has the right multi_tenant_company
    '''
    def deco_f(f):

        @wraps(f)
        def wrap_f(self, info, instance, data=None):
            # If data contains a multi-tenant company someone may be trying to tamper.
            # Dont raise an error, just remove the key silently.
            if data:
                try:
                    del data['multi_tenant_company']
                except (KeyError, AttributeError):
                    pass

            # If the instance is not owned by the user, raise a permission-error.
            if not instance.multi_tenant_company == self.get_multi_tenant_company(info):
                raise PermissionDenied("A user can only update objects that they own.")

            kwargs = {
                'info': info,
                'instance': instance,
            }

            if data:
                kwargs['data'] = data

            return f(self, **kwargs)

        return wrap_f

    return deco_f


class GetMultiTenantCompanyMixin:
    def get_multi_tenant_company(self, info: Info):
        return info.context.request.user.multi_tenant_company


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


class TypeMultiTenantFilterMixin(StrawberryMultitenantMixin):
    pass


def create(type):
    extensions = [IsAuthenticated()]
    return CreateMutation(type, extensions=extensions)


def update(type):
    extensions = [IsAuthenticated()]
    return UpdateMutation(type, extensions=extensions)


def delete():
    extensions = [IsAuthenticated()]
    return DeleteMutation(strawberry_django.NodeInput, extensions=extensions)


def field(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def connection(*args, **kwargs):
    extensions = [IsAuthenticated()]
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
