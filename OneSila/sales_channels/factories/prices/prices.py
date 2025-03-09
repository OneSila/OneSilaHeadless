from products.models import Product
from sales_channels.factories.mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin


class RemotePriceUpdateFactory(ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = Product
    local_product_map = 'local_instance'

    def __init__(self, sales_channel, local_instance, remote_product, api=None):
        super().__init__(sales_channel, local_instance, api=api, remote_product=remote_product)
        self.discounted_price = None
        self.full_price = None
        self.remote_instance = None

    def preflight_check(self):
        """
        Checks that the RemoteProduct and associated SalesChannelViewAssign exist before proceeding.
        Also sets the remote_instance if conditions are met.
        """
        if not self.sales_channel.sync_prices:
            return

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        # Set the remote_instance for the factory based on existing data
        try:
            self.remote_instance = self.remote_model_class.objects.get(
                remote_product=self.remote_product
            )
        except self.remote_model_class.DoesNotExist:
            return False

        self.full_price, self.discounted_price = self.local_instance.get_price_for_sales_channel(self.sales_channel)

        # Convert price and discount to float if they are not None
        if self.full_price is not None:
            self.full_price = float(self.full_price)
        if self.discounted_price is not None:
            self.discounted_price = float(self.discounted_price)

        # If the remote instance already has the correct price, no update is needed
        if self.remote_instance.price == self.full_price and self.remote_instance.discount_price == self.discounted_price:
            return False

        return True

    def get_remote_instance(self):
        """
        Override to prevent fetching in the default way since it is already set in preflight_check.
        """
        pass

    def needs_update(self):
        return True # the actual check is done in preflight_check