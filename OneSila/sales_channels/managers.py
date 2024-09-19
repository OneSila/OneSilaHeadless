from core.managers import MultiTenantManager, MultiTenantQuerySet
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

class RemoteProductConfiguratorQuerySet(PolymorphicQuerySet, MultiTenantQuerySet):
    """
    QuerySet for RemoteProductConfigurator with multitenancy and polymorphic support.
    """

    def create_from_remote_product(self, remote_product, rule=None, variations=None):
        """
        Creates a RemoteProductConfigurator from a remote_product, rule, and variations.
        """
        local_product = remote_product.local_instance
        sales_channel = remote_product.sales_channel

        # Get the product rule if not provided
        if rule is None:
            rule = local_product.get_product_rule()

        if rule is None:
            raise ValueError(f"No product properties rule found for {local_product.name}")

        all_remote_props = self.model._get_all_remote_properties(
            local_product, sales_channel, rule=rule, variations=variations
        )

        # Create the configurator
        configurator = self.create(remote_product=remote_product, multi_tenant_company=remote_product.multi_tenant_company, sales_channel=sales_channel)
        configurator.remote_properties.set(all_remote_props)
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