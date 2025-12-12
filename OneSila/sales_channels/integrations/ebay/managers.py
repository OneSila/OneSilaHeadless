from core.managers import MultiTenantManager, MultiTenantQuerySet
from core.managers.search import SearchManagerMixin, SearchQuerySetMixin
from django.db.models import BooleanField, Case, Value, When
from django.db.models import Manager as DjangoManager
from django.db.models import QuerySet as DjangoQuerySet
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from sales_channels.managers import (
    _MappingManagerMixin,
    _MappingQuerySetMixin,
    _RemotePropertyUsedInProductsQuerySetMixin,
    _RemoteSelectValueUsedInProductsQuerySetMixin,
)


class EbayPropertyQuerySet(
    _RemotePropertyUsedInProductsQuerySetMixin,
    _MappingQuerySetMixin,
    PolymorphicQuerySet,
    MultiTenantQuerySet,
):
    mapped_field = "remote_id"

    def used_in_products(self, value: bool = True):
        from sales_channels.integrations.ebay.models import EbayProductProperty

        return super().used_in_products(
            remote_product_property_model=EbayProductProperty,
            used=value,
        )


class EbayInternalPropertyQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"


class EbayPropertySelectValueQuerySet(
    _RemoteSelectValueUsedInProductsQuerySetMixin,
    _MappingQuerySetMixin,
    MultiTenantQuerySet,
):
    mapped_field = "remote_id"

    def annotate_mapping(self):
        base = super().annotate_mapping()
        return base.annotate(
            ebay_property_mapped_locally=Case(
                When(ebay_property__local_instance__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def filter_ebay_property_mapped_locally(self, value: bool = True):
        return self.annotate_mapping().filter(ebay_property_mapped_locally=value)

    def used_in_products(self, value: bool = True):
        from sales_channels.integrations.ebay.models import EbayProductProperty

        return super().used_in_products_by_remote_property(
            remote_product_property_model=EbayProductProperty,
            used=value,
            related_remote_property_field="ebay_property",
        )

    def filter_ebay_property_used_in_products(self, value: bool = True):
        from sales_channels.integrations.ebay.models import EbayProductProperty

        return super().remote_property_used_in_products(
            remote_product_property_model=EbayProductProperty,
            related_remote_property_field="ebay_property",
            used=value,
        )


class EbayProductTypeQuerySet(_MappingQuerySetMixin, MultiTenantQuerySet):
    mapped_field = "remote_id"


class EbayPropertyManager(_MappingManagerMixin, PolymorphicManager, MultiTenantManager):
    queryset_class = EbayPropertyQuerySet


class EbayInternalPropertyManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = EbayInternalPropertyQuerySet


class EbayPropertySelectValueManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = EbayPropertySelectValueQuerySet


class EbayProductTypeManager(_MappingManagerMixin, MultiTenantManager):
    queryset_class = EbayProductTypeQuerySet


class EbayCategoryQuerySet(SearchQuerySetMixin, DjangoQuerySet):
    pass


class EbayCategoryManager(SearchManagerMixin, DjangoManager):
    def get_queryset(self):
        return EbayCategoryQuerySet(self.model, using=self._db)
