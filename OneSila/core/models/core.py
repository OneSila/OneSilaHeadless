from django.db.models import *
from django.db.models import Model as OldModel
from dirtyfields import DirtyFieldsMixin
from core.models.multi_tenant import MultiTenantAwareMixin

import logging
logger = logging.getLogger(__name__)


class OnlySaveOnChangeMixin(DirtyFieldsMixin, OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def save(self, *args, force_save=False, **kwargs):
        # https://github.com/romgar/django-dirtyfields
        # Checking FK's requires a setting: https://django-dirtyfields.readthedocs.io/en/stable/advanced.html#checking-foreign-key-fields
        if self.is_dirty(check_relationship=True) or force_save:
            super().save(*args, **kwargs)

    def is_dirty_field(self, field):
        return field in self.get_dirty_fields().keys()

    def is_any_field_dirty(self, fields: list) -> bool:
        return any(self.is_dirty_field(field) for field in fields)

    class Meta:
        abstract = True


class TimeStampMixin(OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Model(OnlySaveOnChangeMixin, TimeStampMixin, MultiTenantAwareMixin, OldModel):
    class Meta:
        abstract = True


class SetStatusMixin(Model):
    def set_status(self, status, save=True):
        self.status = status

        if save:
            self.save()

    class Meta:
        abstract = True


class SharedModel(TimeStampMixin, OldModel):
    class Meta:
        abstract = True
