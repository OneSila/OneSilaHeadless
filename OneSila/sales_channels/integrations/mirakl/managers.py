from copy import deepcopy

from django.core.exceptions import ValidationError
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

    def duplicate_for_local_instance(self, *, source, local_instance):
        from sales_channels.integrations.mirakl.models import MiraklProperty

        if source is None:
            raise ValidationError("Source Mirakl property select value is required.")

        if local_instance is None:
            raise ValidationError("Target local property select value is required.")

        remote_property = getattr(source, "remote_property", None)
        if remote_property is None:
            raise ValidationError("Source Mirakl property select value has no remote property.")

        remote_property = remote_property.get_real_instance()
        if remote_property.representation_type != MiraklProperty.REPRESENTATION_PROPERTY:
            raise ValidationError("Only Mirakl properties with representation type 'property' can be duplicated.")

        if not remote_property.local_instance_id:
            raise ValidationError("Mirakl property must be mapped to a local property before duplicating values.")

        if getattr(local_instance, "property_id", None) != remote_property.local_instance_id:
            raise ValidationError("Target local property select value must belong to the mapped local property.")

        if not source.local_instance_id:
            raise ValidationError("Source Mirakl property select value must already be mapped locally.")

        if source.local_instance_id == local_instance.id:
            raise ValidationError("Source and target local property select values must be different.")

        existing = self.filter(
            remote_property=remote_property,
            local_instance=local_instance,
        ).first()
        if existing is not None:
            raise ValidationError("A Mirakl property select value for this local value already exists.")

        return self.create(
            multi_tenant_company=source.multi_tenant_company,
            sales_channel=source.sales_channel,
            remote_id=source.remote_id,
            successfully_created=source.successfully_created,
            outdated=source.outdated,
            outdated_since=source.outdated_since,
            local_instance=local_instance,
            remote_property=remote_property,
            allow_multiple=source.allow_multiple,
            bool_value=source.bool_value,
            code=source.code,
            value=source.value,
            label_translations=deepcopy(source.label_translations),
            value_label_translations=deepcopy(source.value_label_translations),
            value_list_code=source.value_list_code,
            value_list_label=source.value_list_label,
            raw_data=deepcopy(source.raw_data),
        )
