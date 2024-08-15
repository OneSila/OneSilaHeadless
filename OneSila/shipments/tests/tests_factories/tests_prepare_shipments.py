from core.tests import TestCase, TestWithDemoDataMixin
from shipments.factories import PrepareShipmentsFactory
from orders.models import Order


# class TestPrepareShipmentFactory(TestWithDemoDataMixin, TestCase):
#     def test_prepare_shipment(self):
#         order = Order.objects.filter(
#             multi_tenant_company=self.multi_tenant_company,
#             status=Order.TO_SHIP,
#             orderitem__isnull=False,
#         ).last()

#         f = PrepareShipmentsFactory(order)
#         f.run()
