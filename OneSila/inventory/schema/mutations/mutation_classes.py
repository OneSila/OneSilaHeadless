from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry.relay import from_base64
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation, UpdateMutation
from core.schema.core.mutations import models

import logging
logger = logging.getLogger(__name__)


class MovementMixin:
    app_label = 'inventory'

    def get_instance_from_data(self, data, fieldname):
        instance = data.get(fieldname)
        content_type = ContentType.objects.get_for_model(instance)
        object_id = instance.id
        return instance, object_id, content_type

    def get_movement_from_instance(self, data):
        return self.get_instance_from_data(data, 'movement_from_id')

    def get_movement_to_instance(self, data):
        return self.get_instance_from_data(data, 'movement_to_id')


class CreateInventoryMovementMutation(MovementMixin, CreateMutation, GetCurrentUserMixin):
    def create(self, data: dict[str, Any], *, info: Info):
        data['movement_from'], data['mf_object_id'], data['mf_content_type'] = self.get_movement_from_instance(data)
        data['movement_to'], data['mt_object_id'], data['mt_content_type'] = self.get_movement_to_instance(data)
        return super().create(data=data, info=info)


class UpdateWithPublicIdMutation(MovementMixin, UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: models.Model, data: dict[str, Any]):
        data['movement_from'], data['mf_object_id'], data['mf_content_type'] = self.get_movement_from_instance(data)
        data['movement_to'], data['mt_object_id'], data['mt_content_type'] = self.get_movement_to_instance(data)
        return super().update(data=data, info=info, instance=instance)
