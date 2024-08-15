from core.exceptions import SanityCheckError
from shipments.models import Shipment, ShipmentItemToShip

import logging

logger = logging.getLogger(__name__)


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
        self.order_items = order.orderitem_set.all()
        self.multi_tenant_company = order.multi_tenant_company

    def _sanity_check(self):
        if not self.order.is_to_ship():
            raise SanityCheckError(f"Cannot prepare order with status {self.order.status}")

    @staticmethod
    def unify_bundle_variations(bundle_variations):
        product_qty = {}

        for bv in bundle_variations:
            try:
                product_qty[bv.variation] += bv.quantity
            except KeyError:
                product_qty[bv.variation] = bv.quantity

        return product_qty

    def _set_items_needed(self):
        """For all the items we first need to figure out what products we're actually shipping and how many of them."""
        self.items_needed = {}

        # We exclude dropshipping because they are ordered externally and need no
        # shipping action.
        for order_item in self.order_items.exclude_dropshipping().iterator():

            logger.debug(f"Setting items needed for {order_item=}")

            # Before we can assign any items to shipments we need to figure out
            # how much we actually need of each simple, manufacturable or bundle
            # item.
            quantity_needed = order_item.quantity
            product = order_item.product
            # When we sell items, they can be bundles, manufacturable products, etc..
            # For now, we just want the relevant simple or manufacturable products.
            # really know what we need.
            if product.is_bundle():
                # We need to find all of the deflated simple or manufacturable products
                # recursivly and ship these items.
                bundle_variations = product.deflate_bundle()
                unified_product_qty = self.unify_bundle_variations(bundle_variations)
                # Now that we know how much we need of each bundle item
                # we will adjust is for the qty needed.
                products = {p: q * quantity_needed for p, q in unified_product_qty.items()}
            elif product.is_manufacturable() or product.is_simple():
                products = {product: quantity_needed}
            else:
                raise ValueError(f"Product with type {product.type} is not implemented")

            logger.debug(f"Discovered {product.get_type_display()} {product} items {products=}")

            # Now that we have he qty needed for the products we need to add them all
            # to the class for processing in another step.
            for p, q in products.items():
                try:
                    self.items_needed[p] += q
                except KeyError:
                    self.items_needed[p] = q

            logger.debug(f"{self.items_needed=}")

    def _create_shipments_per_location(self):
        pass

    def run(self):
        try:
            self._sanity_check()
            self._set_items_needed()
            self._create_shipments_per_location()
        except SanityCheckError:
            pass
