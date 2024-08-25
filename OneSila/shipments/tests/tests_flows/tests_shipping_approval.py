from core.tests import TestCaseDemoDataMixin, TestCase
from shipments.flows import inventory_change_trigger_flow, pre_approve_shipping_flow
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from orders.models import Order
from products.models import Product
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU

from inventory.models import Inventory, InventoryLocation
from inventory.demo_data import LOCATION_WAREHOUSE_B

import logging
logger = logging.getLogger(__name__)


class InventoryChangeTriggerFlowTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    """
    When an order doesnt have enough inventory,
    but more shows up later, we offer the shipment
    again for shipping
    """

    def test_inventory_change_trigger_full_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        supplier_product = product.supplier_products.last()
        order_qty = 15
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        Order.objects.filter(id=order.id).update(status=order.AWAIT_INVENTORY)
        order.refresh_from_db()
        location = InventoryLocation.objects.get(multi_tenant_company=self.multi_tenant_company,
            name=LOCATION_WAREHOUSE_B)

        Inventory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            inventorylocation=location,
            quantity=100,
            product=supplier_product)

        inventory_change_trigger_flow(order)
        order.refresh_from_db()
        self.assertEqual(order.SHIPPED, order.status)

    def test_inventory_change_trigger_partial_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        supplier_product = product.supplier_products.last()
        order_qty = 15
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        Order.objects.filter(id=order.id).update(status=order.AWAIT_INVENTORY)
        order.refresh_from_db()
        location = InventoryLocation.objects.get(multi_tenant_company=self.multi_tenant_company,
            name=LOCATION_WAREHOUSE_B)

        Inventory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            inventorylocation=location,
            quantity=1,
            product=supplier_product)

        inventory_change_trigger_flow(order)
        order.refresh_from_db()
        self.assertEqual(order.PENDING_SHIPPING_APPROVAL, order.status)
