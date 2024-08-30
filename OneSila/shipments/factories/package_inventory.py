import logging
logger = logging.getLogger(__name__)


class PackageItemInventoryMoveFactory:
    """te package got an item. That means it is no longer on stock
    in the inventory location."""

    def __init__(self, *, package, quantity_received, movement_from):
        self.package = package
        self.quantity_received = quantity_received
        self.movement_from = movement_from
        self.multi_tenant_company = package.multi_tenant_company
        self.product = movement_from.product
        self.inventory = movement_from

    def create_packageitem(self):
        self.packageitem = self.package.packageitem_set.create(
            multi_tenant_company=self.multi_tenant_company,
            quantity=self.quantity_received,
            inventory=self.inventory,
            product=self.product,
        )

    def run(self):
        self.create_packageitem()
