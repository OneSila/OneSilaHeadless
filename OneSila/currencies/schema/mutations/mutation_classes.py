from strawberry_django.optimizer import DjangoOptimizerExtension

from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation, UpdateMutation
from media.models import Video, Media, Image, File
from core.schema.core.mutations import models


class CreateWithPublicIdMutation(CreateMutation, GetCurrentUserMixin):
    """
    Every create needs to include the company a user is assigned to.
    """

    def create(self, data: dict[str, Any], *, info: Info):
        public_currency = data.get('public_currency', None)
        if public_currency:
            public_currency = public_currency.pk

            to_check = ['name', 'iso_code', 'symbol']
            for c in to_check:
                data[c] = getattr(public_currency, c)


        print(data)
        return super().create(data=data, info=info)

class UpdateWithPublicIdMutation(UpdateMutation, GetCurrentUserMixin):
    """
    Every create needs to include the company a user is assigned to.
    """

    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        public_currency = data.get('public_currency', None)
        if public_currency:
            public_currency = public_currency.pk

            to_check = ['name', 'iso_code', 'symbol']
            for c in to_check:
                val = getattr(public_currency, c)
                if getattr(instance, c) != val:
                    setattr(instance, c, val)

        return super().update(data=data, info=info, instance=instance)