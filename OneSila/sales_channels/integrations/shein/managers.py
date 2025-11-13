from core.managers import MultiTenantManager, MultiTenantQuerySet
from django.db.models import BooleanField, Case, Value, When
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from sales_channels.managers import _MappingManagerMixin, _MappingQuerySetMixin


class SheinPropertyQuerySet(_MappingQuerySetMixin, PolymorphicQuerySet, MultiTenantQuerySet):
    mapped_field = "remote_id"


class SheinInternalPropertyQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"


class SheinPropertySelectValueQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"

    def annotate_mapping(self):
        base = super().annotate_mapping()
        return base.annotate(
            renote_property_mapped_locally=Case(
                When(remote_property__local_instance__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def filter_shein_property_mapped_locally(self, value: bool = True):
        return self.annotate_mapping().filter(shein_property_mapped_locally=value)


class SheinProductTypeQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"


class SheinPropertyManager(_MappingManagerMixin, PolymorphicManager, MultiTenantManager):
    queryset_class = SheinPropertyQuerySet


class SheinInternalPropertyManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = SheinInternalPropertyQuerySet


class SheinPropertySelectValueManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = SheinPropertySelectValueQuerySet


class SheinProductTypeManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = SheinProductTypeQuerySet