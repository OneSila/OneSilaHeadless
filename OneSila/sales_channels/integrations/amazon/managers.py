from core.managers import MultiTenantManager, MultiTenantQuerySet
from django.db.models import BooleanField, Case, Value, When
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet


class _MappingQuerySetMixin:
    mapped_field: str

    def annotate_mapping(self):
        return self.annotate(
            mapped_locally=Case(
                When(local_instance__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            mapped_remotely=Case(
                When(**{f"{self.mapped_field}__isnull": False}, then=Value(True)),
                When(**{f"{self.mapped_field}__exact": ""}, then=Value(False)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

    def filter_mapped_locally(self, value: bool = True):
        return self.annotate_mapping().filter(mapped_locally=value)

    def filter_mapped_remotely(self, value: bool = True):
        return self.annotate_mapping().filter(mapped_remotely=value)


class AmazonPropertyQuerySet(_MappingQuerySetMixin, PolymorphicQuerySet, MultiTenantQuerySet):
    mapped_field = "code"


class AmazonPropertySelectValueQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_value"

    def annotate_mapping(self):
        base = super().annotate_mapping()
        return base.annotate(
            amazon_property_mapped_locally=Case(
                When(amazon_property__local_instance__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def filter_amazon_property_mapped_locally(self, value: bool = True):
        return self.annotate_mapping().filter(amazon_property_mapped_locally=value)


class AmazonProductTypeQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "product_type_code"


class _MappingManagerMixin:
    queryset_class = None

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db).annotate_mapping()

    def filter_mapped_locally(self, value: bool = True):
        return self.get_queryset().filter_mapped_locally(value)

    def filter_mapped_remotely(self, value: bool = True):
        return self.get_queryset().filter_mapped_remotely(value)


class AmazonPropertyManager(_MappingManagerMixin, PolymorphicManager, MultiTenantManager):
    queryset_class = AmazonPropertyQuerySet


class AmazonPropertySelectValueManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = AmazonPropertySelectValueQuerySet


class AmazonProductTypeManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = AmazonProductTypeQuerySet

    def get_or_create_from_local_instance(self, *, local_instance, sales_channel):
        return self.get_or_create(
            multi_tenant_company=local_instance.multi_tenant_company,
            local_instance=local_instance,
            sales_channel=sales_channel,
            defaults={
                "name": local_instance.product_type.value,
                "imported": False,
            },
        )

