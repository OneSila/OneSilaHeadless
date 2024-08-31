from core.tests import TestCase, TransactionTestCase, \
    TransactionTestCaseMixin, TestWithDemoDataMixin
from model_bakery import baker
from OneSila.schema import schema
from lead_times.models import LeadTime, LeadTimeForShippingAddress, \
    LeadTimeProductOutOfStock
from contacts.models import ShippingAddress, Supplier
from products.models import Product, SupplierProduct


class LeadTimeQueriesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_lead_time_create(self):
        query = """
            mutation createLeadTime($unit: Int!, $minTime: Int!, $maxTime: Int!) {
              createLeadTime(
                data: {unit: $unit, minTime: $minTime, maxTime: $maxTime}
              ) {
                id
                unit
              }
            }
        """
        unit = LeadTime.WEEK
        min_time = 5
        max_time = 10

        resp = self.strawberry_test_client(
            query=query,
            variables={
                'unit': unit,
                'minTime': min_time,
                'maxTime': max_time,
            },
        )
        self.assertTrue(resp.errors is None)


class LeadTimeForShippingAddressTestCase(TestWithDemoDataMixin, TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.lead_time, _ = LeadTime.objects.get_or_create(min_time=1, max_time=10, unit=LeadTime.DAY,
            multi_tenant_company=self.multi_tenant_company)
        self.shipping_address = ShippingAddress.objects.filter(multi_tenant_company=self.multi_tenant_company).last()
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)

    def test_leadtime_for_shippingaddress(self):
        from .mutations import create_leadtime_for_shippingaddress
        from lead_times.schema.types.types import LeadTimeForShippingAddressType, LeadTimeType
        shippingid = self.to_global_id(instance=self.shipping_address)
        leadtimeid = self.to_global_id(instance=self.lead_time)

        LeadTimeForShippingAddress.objects.\
            filter(shippingaddress=self.shipping_address, multi_tenant_company=self.multi_tenant_company).\
            delete()

        resp = self.strawberry_test_client(
            query=create_leadtime_for_shippingaddress,
            variables={'shippingid': shippingid, 'leadtimeid': leadtimeid})
        self.assertTrue(resp.errors is None)


class LeadTimeProductOutOfStockTestCase(LeadTimeForShippingAddressTestCase):
    def setUp(self):
        super().setUp()
        self.supplier_product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")

    def test_lead_time_product_outofstock(self):
        from .mutations import create_lead_time_product_outofstock
        from lead_times.schema.types.types import LeadTimeProductOutOfStockType, LeadTimeType

        productid = self.to_global_id(instance=self.supplier_product)
        leadtimeid = self.to_global_id(instance=self.lead_time)

        LeadTimeProductOutOfStock.objects.\
            filter(product=self.supplier_product, multi_tenant_company=self.multi_tenant_company).\
            delete()

        resp = self.strawberry_test_client(
            query=create_lead_time_product_outofstock,
            variables={'productid': productid, 'leadtimeid': leadtimeid})
        self.assertTrue(resp.errors is None)
