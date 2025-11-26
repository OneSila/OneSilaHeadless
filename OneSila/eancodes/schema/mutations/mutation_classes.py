from django.db import IntegrityError
from strawberry_django.optimizer import DjangoOptimizerExtension

from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation, UpdateMutation
from django.utils.translation import gettext_lazy as _
from eancodes.models import EanCode
from eancodes.signals import ean_code_released_for_product
from eancodes.tasks import eancodes__ean_code__generate_task


class GenerateEancodesMutation(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):

        with DjangoOptimizerExtension.disabled():

            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            prefix = data.get("prefix", None)

            if prefix is None:
                raise IntegrityError(_("Please provide a prefix"))

            if not isinstance(prefix, str) or not prefix.isdigit():
                raise IntegrityError(_("Prefix should be containing only numbers"))

            if not (7 <= len(prefix) <= 12):
                raise IntegrityError(_("Prefix should have a length between 7 and 12 characters"))

            eancodes__ean_code__generate_task(prefix=prefix, multi_tenant_company=multi_tenant_company)

            return None


class AssignEanCodeMutation(CreateMutation, GetCurrentUserMixin):
    def create(self, data: dict[str, Any], *, info: Info):
        multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)

        prod = data.get("product", None)
        if prod is None:
            raise IntegrityError(_("Please provide a product"))

        product = prod.pk
        to_assign = EanCode.objects.filter_multi_tenant(multi_tenant_company=multi_tenant_company).filter(
            internal=True, already_used=False, product__isnull=True).order_by('ean_code').first()

        if to_assign is None:
            raise IntegrityError(_("There is no available EAN code to be assigned."))

        to_assign.product = product
        to_assign.save()

        return to_assign


class ReleaseEanCodeMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: EanCode, data: dict[str, Any]):

        old_product = None
        if instance.product is not None:
            old_product = instance.product

        instance.product = None
        instance.already_used = True
        instance.save()

        if old_product is not None:
            ean_code_released_for_product.send(sender=old_product.__class__, instance=old_product)

        return instance
