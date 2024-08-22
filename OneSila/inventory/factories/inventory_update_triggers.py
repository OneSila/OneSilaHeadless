from products.models import Product, ConfigurableVariation, BundleVariation, SupplierProduct
from inventory.signals import product_inventory_change


import logging
logger = logging.getLogger(__name__)


class InventoryUpdateTriggerFactory:
    """
    Trigger a signal for both the products related to the inventory product
    and the product and their real proxy product type.
    """
    signal = product_inventory_change

    def __init__(self, inventory):
        self.inventory = inventory
        self.product = inventory.product
        self.multi_tenant_company = inventory.multi_tenant_company

    def get_parent_product_ids(self, product):
        product_ids = set()
        product_ids.add(product.id)

        for prod in product.base_products.all().iterator():
            product_ids.add(prod.id)

        bundles = BundleVariation.objects.filter(variation_id__in=product_ids)
        for bv in bundles.iterator():
            product_ids.add(bv.parent.id)

            logging.debug(f"Is this a bundle? {bv.parent=}?  {bv.parent.is_bundle()}")

            if bv.parent.is_bundle():
                product_ids.update(self.get_parent_product_ids(bv.parent))

        return product_ids

    def set_product_qs(self):
        parent_product_ids = self.get_parent_product_ids(self.product)
        self.product_qs = Product.objects.filter(id__in=parent_product_ids)

    def trigger_all_signals(self):
        for product in self.product_qs.iterator():
            real_product = product.get_proxy_instance()
            self.signal.send(sender=product.__class__, instance=product)
            self.signal.send(sender=real_product.__class__, instance=real_product)

    def run(self):
        self.set_product_qs()
        self.trigger_all_signals()
