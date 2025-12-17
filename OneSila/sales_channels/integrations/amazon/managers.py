from django.db.models import Case, When, Value, BooleanField

from core.managers import MultiTenantManager, MultiTenantQuerySet
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet
from sales_channels.managers import (
    _MappingManagerMixin,
    _MappingQuerySetMixin,
    _RemotePropertyUsedInProductsQuerySetMixin,
    _RemoteSelectValueUsedInProductsQuerySetMixin,
)


class AmazonPropertyQuerySet(
    _RemotePropertyUsedInProductsQuerySetMixin,
    _MappingQuerySetMixin,
    PolymorphicQuerySet,
    MultiTenantQuerySet,
):
    mapped_field = "code"

    def used_in_products(self, value: bool = True):
        from sales_channels.integrations.amazon.models import AmazonProductProperty

        return super().used_in_products(
            remote_product_property_model=AmazonProductProperty,
            used=value,
        )


class AmazonPropertySelectValueQuerySet(
    _RemoteSelectValueUsedInProductsQuerySetMixin,
    _MappingQuerySetMixin,
    MultiTenantQuerySet,
):
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

    def used_in_products(self, value: bool = True):
        from sales_channels.integrations.amazon.models import AmazonProductProperty

        return super().used_in_products_by_remote_property(
            remote_product_property_model=AmazonProductProperty,
            used=value,
            related_remote_property_field="amazon_property",
        )

    def filter_amazon_property_used_in_products(self, value: bool = True):
        from sales_channels.integrations.amazon.models import AmazonProductProperty

        return super().remote_property_used_in_products(
            remote_product_property_model=AmazonProductProperty,
            related_remote_property_field="amazon_property",
            used=value,
        )


class AmazonProductTypeQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "product_type_code"


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
