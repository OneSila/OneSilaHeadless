import logging
logger = logging.getLogger(__name__)


class PackageItemInventoryMoveFactory:
    """te package got an item. That means it is no longer on stock
    in the inventory location."""

    def __init__(self, packageitem):
        self.packageitem = packageitem
        self.inventory = packageitem.inventory

    def reduce_inventory(self):
        reduce_with = self.packageitem.quantity
        self.inventory.reduce_quantity(reduce_with)

    def run(self):
        self.reduce_inventory()
