from products.models import Product, ConfigurableVariation, BundleVariation, SupplierProduct
from inventory.signals import inventory_change


import logging
logger = logging.getLogger(__name__)


class InventoryChangeProductUpdateTriggerFactory:
    """
    Trigger a signal for both the products related to the inventory product
    and the product and their real proxy product type.
    """
    signal = inventory_change

    def __init__(self, inventory):
        self.inventory = inventory
        self.product = inventory.product
        self.multi_tenant_company = inventory.multi_tenant_company

    def get_parent_product_ids(self, product):
        return product.get_parent_products()

    def set_product_qs(self):
        self.product_qs = self.get_parent_product_ids(self.product)

    def trigger_all_signals(self):
        for product in self.product_qs.iterator():
            real_product = product.get_proxy_instance()
            self.signal.send(sender=product.__class__, instance=product)
            self.signal.send(sender=real_product.__class__, instance=real_product)

    def run(self):
        self.set_product_qs()
        self.trigger_all_signals()
