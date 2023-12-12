from strawberry import UNSET

from strawberry.relay.utils import from_base64
from strawberry_django.resolvers import django_resolver
from strawberry_django.mutations import resolvers
from strawberry_django.auth.utils import get_current_user
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry_django.utils.requests import get_request

from django.db import transaction
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.conf import settings

from asgiref.sync import async_to_sync

from channels import auth as channels_auth

from core.schema.core.mutations import create, type, DjangoUpdateMutation, \
    DjangoCreateMutation, GetMultiTenantCompanyMixin, default_extensions, \
    update, Info, models, Iterable, Any, IsAuthenticated
from core.factories.multi_tenant import InviteUserFactory, RegisterUserFactory, \
    AcceptUserInviteFactory, EnableUserFactory, DisableUserFactory


class CleanupDataMixin:
    def cleanup_data(self, data):
        for k in data.copy().keys():
            if data[k] is UNSET:
                del data[k]

        return data


class InviteUserMutation(CleanupDataMixin, GetMultiTenantCompanyMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info)
        data = self.cleanup_data(data)

        with DjangoOptimizerExtension.disabled():
            fac = InviteUserFactory(
                multi_tenant_company=multi_tenant_company,
                **data)
            fac.run()
            return fac.user


class AcceptInvitationMutation(DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        # Do not optimize anything while retrieving the object to update
        with DjangoOptimizerExtension.disabled():
            fac = AcceptUserInviteFactory(
                user=instance,
                password=data['password'],
                language=data['language'])
            fac.run()

            return fac.user


class MyMultiTenantCompanyCreateMutation(GetMultiTenantCompanyMixin, DjangoCreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        model = self.django_model
        assert model is not None

        user = get_current_user(info)

        with DjangoOptimizerExtension.disabled():
            obj = resolvers.create(
                info,
                model,
                data,
                full_clean=self.full_clean,
            )

            user.multi_tenant_company = obj
            user.save()

            return obj


class MyMultiTentantCompanyUpdateMutation(GetMultiTenantCompanyMixin, DjangoUpdateMutation):
    """
    This mutation will only protect against having a multi-tentant company.
    Not the existance on the model, since the MultiTenantCompany has no reference to itself.
    """
    @django_resolver
    @transaction.atomic
    def resolver(self, source: Any, info: Info, args: list[Any], kwargs: dict[str, Any],) -> Any:
        model = self.django_model
        assert model is not None

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = self.get_multi_tenant_company(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


class UpdateMeMutation(DjangoUpdateMutation):
    @django_resolver
    @transaction.atomic
    def resolver(self, source: Any, info: Info, args: list[Any], kwargs: dict[str, Any],) -> Any:
        model = self.django_model
        assert model is not None

        data: Any = kwargs.get(self.argument_name)
        vdata = vars(data).copy() if data is not None else {}
        instance = get_current_user(info)

        return self.update(info, instance, resolvers.parse_input(info, vdata))


class DisableUserMutation(DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        # Do not optimize anything while retrieving the object to update
        with DjangoOptimizerExtension.disabled():
            fac = DisableUserFactory(user=instance)
            fac.run()
            return fac.user


class EnableUserMutation(DjangoUpdateMutation):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        # Do not optimize anything while retrieving the object to update
        with DjangoOptimizerExtension.disabled():
            fac = EnableUserFactory(user=instance)
            fac.run()

            instance.refresh_from_db()
            return instance
