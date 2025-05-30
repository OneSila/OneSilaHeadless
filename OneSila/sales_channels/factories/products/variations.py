from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory
from sales_channels.models.products import RemoteProduct
from sales_channels.models.sales_channels import SalesChannelViewAssign


class RemoteProductVariationAddFactory(RemoteInstanceUpdateFactory):
    create_if_not_exists = True
    create_factory_class = None

    def __init__(self, sales_channel, local_instance, parent_product, api=None, skip_checks=False, remote_instance=None, remote_parent_product=None, configurator_properties=None):
        self.local_instance = local_instance
        self.sales_channel = sales_channel
        self.parent_product = parent_product
        self.remote_instance = remote_instance
        self.remote_parent_product = remote_parent_product  # Will be set in the preflight_check
        self.skip_checks = skip_checks

        # in order to not get them on every add variation we can predefine this as the remote properties used in configurator
        self.configurator_properties = configurator_properties
        if self.skip_checks and (self.remote_instance is None or self.remote_parent_product is None):
            raise ValueError("Factory have skip checks enabled without giving the remote instances.")

        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance, remote_product=remote_parent_product)

    def preflight_check(self):
        """
        Checks that the RemoteProduct, Remote Parent Product, and associated SalesChannelViewAssign exist before proceeding.
        Also sets the remote_instance if conditions are met.
        """
        if self.skip_checks:
            return True

        # Check for SalesChannelViewAssign associated with the remote parent product
        parent_assign_exists = SalesChannelViewAssign.objects.filter(
            product=self.parent_product,
            sales_channel=self.sales_channel
        ).exists()

        if not parent_assign_exists:
            return False

        # Retrieve the RemoteProduct associated with the parent local product
        try:
            self.remote_parent_product = RemoteProduct.objects.get(
                local_instance=self.parent_product,
                sales_channel=self.sales_channel
            )
        except RemoteProduct.DoesNotExist:
            return False

        # Check if the remote variation product itself exists in the sales channel
        try:
            self.remote_instance = RemoteProduct.objects.get(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel,
                remote_parent_product=self.remote_parent_product
            )
        except RemoteProduct.DoesNotExist:
            if self.create_if_not_exists:
                # this is ok because if the parent product exists + it have an assign it means we need to create it

                factory = self.create_factory_class(
                    sales_channel=self.sales_channel,
                    local_instance=self.local_instance,
                    parent_local_instance=self.parent_product,
                    api=self.api
                )
                factory.run()
                self.remote_instance = factory.remote_instance
            else:
                raise

        return True

    def get_remote_instance(self):
        pass

    def get_remote_product(self, product):
        return self.remote_instance

    def needs_update(self):
        return True  # the actual check is done in preflight_check


class RemoteProductVariationDeleteFactory(RemoteInstanceDeleteFactory):
    """
    Generic factory for deleting a product variation mirror instance.
    """
    local_model_class = Product
