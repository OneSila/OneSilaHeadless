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


class _MappingManagerMixin:
    queryset_class = None

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db).annotate_mapping()

    def filter_mapped_locally(self, value: bool = True):
        return self.get_queryset().filter_mapped_locally(value)

    def filter_mapped_remotely(self, value: bool = True):
        return self.get_queryset().filter_mapped_remotely(value)

class RemoteProductConfiguratorQuerySet(PolymorphicQuerySet, MultiTenantQuerySet):
    """
    QuerySet for RemoteProductConfigurator with multitenancy and polymorphic support.
    """

    def create_from_remote_product(self, remote_product, rule=None, variations=None, amazon_theme=None):
        """
        Creates a RemoteProductConfigurator from a remote_product, rule, and variations.
        """
        local_product = remote_product.local_instance
        sales_channel = remote_product.sales_channel

        # Get the product rule if not provided
        if rule is None:
            rule = local_product.get_product_rule(sales_channel=sales_channel)

        if rule is None:
            raise ValueError(f"No product properties rule found for {local_product.name}")

        all_local_props = self.model._get_all_properties(
            local_product, sales_channel, rule=rule, variations=variations
        )

        configurator = self.create(
            remote_product=remote_product,
            multi_tenant_company=remote_product.multi_tenant_company,
            sales_channel=sales_channel,
            amazon_theme=amazon_theme,
        )
        configurator.properties.set(all_local_props)
        configurator.save()

        return configurator


class RemoteProductConfiguratorManager(PolymorphicManager, MultiTenantManager):
    """
    Manager for RemoteProductConfigurator with multitenancy and polymorphic support.
    """

    def get_queryset(self):
        return RemoteProductConfiguratorQuerySet(self.model, using=self._db)

    # Optionally, expose QuerySet methods directly on the Manager
    def create_from_remote_product(self, *args, **kwargs):
        return self.get_queryset().create_from_remote_product(*args, **kwargs)


class SalesChannelViewQuerySet(PolymorphicQuerySet, MultiTenantQuerySet):
    """QuerySet for :class:`SalesChannelView` with multitenancy and polymorphic support."""


class SalesChannelViewManager(PolymorphicManager, MultiTenantManager):
    """Manager for :class:`SalesChannelView` providing search and multitenancy."""

    def get_queryset(self):
        return SalesChannelViewQuerySet(self.model, using=self._db)


class SalesChannelViewAssignQuerySet(PolymorphicQuerySet, MultiTenantQuerySet):
    """QuerySet for :class:`SalesChannelViewAssign` with multitenancy and polymorphic support."""

    def filter_by_status(self, *, status: str):
        from sales_channels.models.products import RemoteProduct

        normalized_status = (status or "").upper()
        valid_statuses = {
            RemoteProduct.STATUS_COMPLETED,
            RemoteProduct.STATUS_FAILED,
            RemoteProduct.STATUS_PROCESSING,
        }

        if normalized_status not in valid_statuses:
            return self.none()

        return self.filter(remote_product__status=normalized_status)


class SalesChannelViewAssignManager(PolymorphicManager, MultiTenantManager):
    """Manager for :class:`SalesChannelViewAssign` providing search and multitenancy."""

    def get_queryset(self):
        return SalesChannelViewAssignQuerySet(self.model, using=self._db)

    def filter_by_status(self, *, status: str):
        return self.get_queryset().filter_by_status(status=status)
