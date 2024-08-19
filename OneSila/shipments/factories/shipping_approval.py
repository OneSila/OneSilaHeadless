from core.exceptions import SanityCheckError
from orders.models import Order

import logging
logger = logging.getLogger(__name__)


class PreApproveShippingFactory:
    """
    Run a few checks and push the order straight into shipping
    if all items are on stock.  No need for the usual approval.

    If only a few items are available, push into manual_approval_needed
    """

    def __init__(self, order):
        self.order = order
        self.multi_tenant_company = order.multi_tenant_company

    def _sanity_check(self):
        if not self.order.is_pending_processing():
            raise SanityCheckError(f"Cannot pre-approve order {self.order}.  Status is not {Order.PENDING_SHIPPING}")

    def set_order_in_stock(self):
        # If all items are in stock, we can go ahead and ship.
        # else, you must ask for permission.
        in_stock = []

        for item in self.order.orderitem_set.all():
            physical = item.product.inventory.physical()
            needed = item.quantity
            in_stock.append(physical >= needed)

        self.order_in_stock = all(in_stock)

    def mark_order_status(self):
        if self.order_in_stock:
            self.order.set_status_to_ship()
        else:
            self.order.set_status_pending_shipping_approval()

    def run(self):
        self._sanity_check()
        self.set_order_in_stock()
        self.mark_order_status()
