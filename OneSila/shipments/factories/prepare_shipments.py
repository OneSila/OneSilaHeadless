from core.exceptions import SanityCheckError
from shipments.models import Shipment, ShipmentItem


class PrepareShipmentsFactory:
    """
    Preparing an shipment:
    1. depends if the order is ready to ship (locally shippable items have enough inventory)
    2. will create a shipment for every item needed
    3. from any location found.

    This factory is used for both complete and partial orders.
    The actuall shipping will happen in other flows.
    """

    def __init__(self, order):
        self.order = order
        self.multi_tenant_company = order.multi_tenant_company

    def _sanity_check(self):
        if not self.order.is_to_ship():
            raise SanityCheckError(f"Cannot prepare order with status {self.order.status}")

    def _discover_inventory_per_location(self):
        pass

    def _create_shipments_per_location(self):
        pass

    def run(self):
        try:
            self._sanity_check()
            self._discover_inventory_per_location()
            self._create_shipments()
        except SanityCheckError:
            pass
