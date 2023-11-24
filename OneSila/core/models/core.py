from django.db.models import *
from django.db.models import Model as OldModel
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from dirtyfields import DirtyFieldsMixin

from core.validators import phone_regex
from core.models.multi_tenant import MultiTenantCompany, MultiTenantAwareMixin

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

    def is_dirty_field(field):
        return field in self.dirty_fields.keys()

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


class SharedModel(TimeStampMixin, OldModel):
    class Meta:
        abstract = True
