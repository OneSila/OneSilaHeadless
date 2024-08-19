from core.tests import TestCase, TestCaseDemoDataMixin
from products.demo_data import DROPSHIP_PRODUCT_VISCONTI_SKU
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from purchasing.flows.dropshipping_purchases import buy_dropshippingproducts_flow
from products.models import DropshipProduct


class BuyDropshippingProductsTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    def test_buydropshippingproducts_flow(self):
        product = DropshipProduct.objects.get(
            sku=DROPSHIP_PRODUCT_VISCONTI_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_buydropshippingproducts_flow', product, 1)
        order.set_status_processing()

        buy_dropshippingproducts_flow(order)

        self.assertEqual(order.purchaseorder_set.all().count(), 1)
        self.assertTrue(all([i.is_to_order() for i in order.purchaseorder_set.all()]))
