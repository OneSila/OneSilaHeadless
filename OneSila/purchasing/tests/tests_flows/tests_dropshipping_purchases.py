from core.tests import TestCase, TestCaseDemoDataMixin
from products.demo_data import DROPSHIP_PRODUCT_VISCONTI_SKU, DROPSHIP_PRODUCT_JAMES_SKU
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from purchasing.flows.dropshipping_purchases import buy_dropshippingproducts_flow
from products.models import DropshipProduct


class BuyDropshippingProductsTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    def test_buydropshippingproducts_flow(self):
        product = DropshipProduct.objects.get(
            sku=DROPSHIP_PRODUCT_VISCONTI_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_buydropshippingproducts_flow', product, 1)
        order.set_status_pending_processing()

        buy_dropshippingproducts_flow(order)

        self.assertEqual(order.purchaseorder_set.all().count(), 1)
        self.assertTrue(all([i.is_to_order() for i in order.purchaseorder_set.all()]))

    def test_dropshipping_multi_client(self):
        """
        Imagine this case:
        - 2 orders, each with 1 product to a different client but from the same supplier

        When a PO is created, does it create 2 PO’s or does it try to condense them to the open PO?
        - consended = not ok for dropshipping. Will get goods delivered to the wrong adress
        - not consdensed = ok
        """
        product = DropshipProduct.objects.get(
            sku=DROPSHIP_PRODUCT_VISCONTI_SKU, multi_tenant_company=self.multi_tenant_company)
        product_two = DropshipProduct.objects.get(
            sku=DROPSHIP_PRODUCT_JAMES_SKU, multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(product.supplier_products.last().supplier, product_two.supplier_products.last().supplier)

        order = self.create_test_order('test_dropshipping_multi_client_one', product, 1)
        order.set_status_pending_processing()

        order_bis = self.create_test_order('test_dropshipping_multi_client_two', product_two, 1)
        order_bis.set_status_pending_processing()

        buy_dropshippingproducts_flow(order)
        buy_dropshippingproducts_flow(order_bis)

        self.assertEqual(order.purchaseorder_set.all().count(), 1)
        self.assertTrue(all([i.is_to_order() for i in order.purchaseorder_set.all()]))

        self.assertEqual(order.purchaseorder_set.count(), 1)
        self.assertEqual(order_bis.purchaseorder_set.count(), 1)

        self.assertFalse(order_bis.purchaseorder_set.last() == order.purchaseorder_set.last())
