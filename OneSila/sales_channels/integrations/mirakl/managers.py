from django.db.models import BooleanField, Case, Q, Value, When
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from core.managers import MultiTenantManager, MultiTenantQuerySet
from sales_channels.managers import _MappingManagerMixin, _MappingQuerySetMixin


class MiraklPropertyQuerySet(_MappingQuerySetMixin, PolymorphicQuerySet, MultiTenantQuerySet):
    mapped_field = "code"

    def annotate_mapping(self):
        from sales_channels.integrations.mirakl.models import MiraklProperty

        return self.annotate(
            mapped_locally=Case(
                When(local_instance__isnull=False, then=Value(True)),
                When(
                    Q(representation_type=MiraklProperty.REPRESENTATION_DEFAULT_VALUE)
                    & ~Q(default_value=""),
                    then=Value(True),
                ),
                When(
                    ~Q(
                        representation_type__in=[
                            MiraklProperty.REPRESENTATION_PROPERTY,
                            MiraklProperty.REPRESENTATION_CONDITION,
                            MiraklProperty.REPRESENTATION_LOGISTIC_CLASS,
                            MiraklProperty.REPRESENTATION_DEFAULT_VALUE,
                        ]
                    ),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            mapped_remotely=Case(
                When(Q(**{f"{self.mapped_field}__isnull": False}) & ~Q(**{f"{self.mapped_field}__exact": ""}), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )


class MiraklProductTypeQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"


class MiraklPropertySelectValueQuerySet(_MappingQuerySetMixin, PolymorphicQuerySet, MultiTenantQuerySet):
    mapped_field = "remote_id"

    def annotate_mapping(self):
        base = super().annotate_mapping()
        return base.annotate(
            mirakl_property_mapped_locally=Case(
                When(remote_property__local_instance__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def filter_mirakl_property_mapped_locally(self, value: bool = True):
        return self.annotate_mapping().filter(mirakl_property_mapped_locally=value)

    def filter_is_property_value(self, value: bool = True):
        from sales_channels.integrations.mirakl.models import MiraklProperty

        property_ids = MiraklProperty.objects.filter(
            representation_type__in=[
                MiraklProperty.REPRESENTATION_PROPERTY,
                MiraklProperty.REPRESENTATION_CONDITION,
                MiraklProperty.REPRESENTATION_LOGISTIC_CLASS,
                MiraklProperty.REPRESENTATION_PRODUCT_ACTIVE,
                MiraklProperty.REPRESENTATION_ALLOW_BACKORDER,
            ],
        ).values_list("id", flat=True)

        lookup = {"remote_property_id__in": property_ids}
        if value:
            return self.filter(**lookup)
        return self.exclude(**lookup)


class MiraklPropertyManager(_MappingManagerMixin, PolymorphicManager, MultiTenantManager):
    queryset_class = MiraklPropertyQuerySet


class MiraklProductTypeManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = MiraklProductTypeQuerySet


class MiraklPropertySelectValueManager(_MappingManagerMixin, PolymorphicManager, MultiTenantManager):
    queryset_class = MiraklPropertySelectValueQuerySet
