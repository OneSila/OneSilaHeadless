from django.db import models, transaction
from django.core.exceptions import PermissionDenied

import strawberry_django
from strawberry_django.mutations import resolvers
from strawberry_django.permissions import IsAuthenticated

from strawberry_django.mutations.fields import DjangoCreateMutation, \
    DjangoUpdateMutation, DjangoDeleteMutation, get_pk
from typing import TYPE_CHECKING, Any, Iterable, Union, Callable
from strawberry.types import Info
from strawberry import type, field
from typing import List

from .decorators import multi_tenant_owner_protection
from .mixins import GetMultiTenantCompanyMixin, GetCurrentUserMixin
from .extensions import default_extensions
from ...signals import mutation_update, mutation_create
from strawberry_django.permissions import get_with_perms


class BulkDjangoDeleteMutation(DjangoDeleteMutation):
    """
    Enhanced Delete Mutation to support both single and bulk deletions.
    """

    @transaction.atomic
    def resolver(
        self,
        source: Any,
        info: Info | None,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        assert info is not None

        # Retrieve the deletion data
        data = kwargs.get(self.argument_name)

        # If bulk, ensure data is a list and process each item
        if isinstance(data, list):
            results = []
            for item in data:
                vdata = vars(item).copy()
                pk = get_pk(vdata, key_attr=self.key_attr)

                # Retrieve the instance
                instance = get_with_perms(
                    pk,
                    info,
                    required=True,
                    model=self.django_model,
                    key_attr=self.key_attr,
                )

                # Perform the delete operation
                deleted_instance = self.delete(
                    info, instance, resolvers.parse_input(info, vdata, key_attr=self.key_attr)
                )
                results.append(deleted_instance)

            return results  # Return the list of deleted items

        # Handle single deletion
        vdata = vars(data).copy() if data is not None else {}
        pk = get_pk(vdata, key_attr=self.key_attr)
        instance = get_with_perms(
            pk,
            info,
            required=True,
            model=self.django_model,
            key_attr=self.key_attr,
        )
        return self.delete(
            info, instance, resolvers.parse_input(info, vdata, key_attr=self.key_attr)
        )


class CreateMutation(GetMultiTenantCompanyMixin, GetCurrentUserMixin, DjangoCreateMutation):
    """
    Every create needs to include the company a user is assigned to.
    """

    def __init__(self, *args, validators: list[Callable[[dict[str, Any], Info], None]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators = validators or []

    def run_validations(self, data: dict[str, Any], info: Info):
        for validator in self.validators:
            validator(data, info)

    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
        multi_tenant_user = self.get_current_user(info, fail_silently=False)
        data['multi_tenant_company'] = multi_tenant_company
        data['created_by_multi_tenant_user'] = multi_tenant_user
        data['last_update_by_multi_tenant_user'] = multi_tenant_user
        self.run_validations(data, info)
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


class DeleteMutation(GetMultiTenantCompanyMixin, BulkDjangoDeleteMutation):
    """
    You can only delete if the object is owned by the comnpany represented
    """
    @multi_tenant_owner_protection()
    def delete(self, info: Info, instance: models.Model | Iterable[models.Model]):
        return super().delete(info=info, instance=instance)


def create(input_type, validators=None):
    extensions = default_extensions
    return CreateMutation(input_type, extensions=extensions, validators=validators)


def update(input_type):
    extensions = default_extensions
    return UpdateMutation(input_type, extensions=extensions)


def delete(is_bulk=False):

    input_type = List[strawberry_django.NodeInput] if is_bulk else strawberry_django.NodeInput
    extensions = default_extensions
    return DeleteMutation(input_type, extensions=extensions)
