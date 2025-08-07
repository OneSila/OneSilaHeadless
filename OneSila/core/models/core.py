from django.db.models import *
from django.db.models import Model as OldModel
from dirtyfields import DirtyFieldsMixin
from core.models.multi_tenant import MultiTenantAwareMixin
from strawberry.relay import to_base64
from get_absolute_url.helpers import reverse_lazy

import logging
logger = logging.getLogger(__name__)


class GlobalIDMixin(OldModel):
    @property
    def global_id(self):
        type_name = f"{self.__class__.__name__}Type"
        return to_base64(type_name, self.id)

    class Meta:
        abstract = True


class GetAbsoluteURLMixin:
    def get_absolute_url(self):
        """
        Get the absolute url for the product. Keep in mind that the PK is a UUID for graphql.
        """
        # Get the url string from the class Meta.url_detail_page_string
        try:
            url_string = self._meta.url_detail_page_string
            return reverse_lazy(url_string, kwargs={'pk': self.global_id})
        except AttributeError:
            return None


class OnlySaveOnChangeMixin(DirtyFieldsMixin, OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def save(self, *args, force_save=False, **kwargs):
        # https://github.com/romgar/django-dirtyfields
        # Checking FK's requires a setting: https://django-dirtyfields.readthedocs.io/en/stable/advanced.html#checking-foreign-key-fields
        if self.is_dirty(check_relationship=True) or force_save:
            super().save(*args, **kwargs)

    def is_dirty_field(self, field, check_relationship=False):
        return field in self.get_dirty_fields(check_relationship=check_relationship).keys()

    def is_any_field_dirty(self, fields: list, check_relationship=False) -> bool:
        return any(self.is_dirty_field(field, check_relationship=check_relationship) for field in fields)

    class Meta:
        abstract = True


class TimeStampMixin(OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Model(GlobalIDMixin, OnlySaveOnChangeMixin, TimeStampMixin, MultiTenantAwareMixin, GetAbsoluteURLMixin, OldModel):
    class Meta:
        abstract = True


class SetStatusMixin(Model):
    def set_status(self, status, save=True):
        self.status = status

        if save:
            self.save()

    class Meta:
        abstract = True


class SharedModel(GlobalIDMixin, TimeStampMixin, OldModel):
    class Meta:
        abstract = True
