from core.tests import TestCase, TestWithDemoDataMixin
from contacts.models import ShippingAddress, Supplier
from inventory.models import InventoryLocation, Inventory
from products.models import SimpleProduct, SupplierProduct
from lead_times.models import LeadTime, LeadTimeForShippingAddress, \
    LeadTimeProductOutOfStock


class LeadTimeManagerTestCase(TestWithDemoDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.lead_time_fast, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=4, unit=LeadTime.HOUR)
        self.lead_time_overlap, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=2, max_time=5, unit=LeadTime.HOUR)
        self.lead_time_slow, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=2, unit=LeadTime.DAY)

    def test_filter_fastest(self):
        filtered = LeadTime.objects.\
            filter_fastest([self.lead_time_fast.id, self.lead_time_overlap.id, self.lead_time_slow.id])

        self.assertEqual(filtered, self.lead_time_fast)

    def test_filter_fastest_qs(self):
        filtered = LeadTime.objects.filter(multi_tenant_company=self.multi_tenant_company)
        fastest = filtered.filter_fastest()

        self.assertEqual(fastest, self.lead_time_fast)

    def test_leadtime_for_outofstock_product(self):
        product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        LeadTimeProductOutOfStock.objects.create(multi_tenant_company=self.multi_tenant_company,
            product=product, leadtime_outofstock=self.lead_time_slow)

        lead_time_resp = LeadTime.objects.get_product_leadtime(product)

        self.assertEqual(lead_time_resp, self.lead_time_slow)

    def test_lead_time_for_inventories(self):
        supplier = Supplier.objects.filter(multi_tenant_company=self.multi_tenant_company).last()
        shippingaddress = ShippingAddress.objects.filter(
            company=supplier,
            multi_tenant_company=self.multi_tenant_company).last()

        inventory_location, _ = InventoryLocation.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            name='for_inv_test', shippingaddress=shippingaddress)
        leadtime_for_shipping_address, _ = LeadTimeForShippingAddress.objects.get_or_create(shippingaddress=shippingaddress,
            multi_tenant_company=self.multi_tenant_company)

        leadtime_for_shipping_address.leadtime = self.lead_time_overlap
        leadtime_for_shipping_address.save()
        leadtime_for_shipping_address.refresh_from_db()

        self.assertEqual(leadtime_for_shipping_address.leadtime, self.lead_time_overlap)

        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company,
            supplier=supplier)
        supplier_product.base_products.add(simple)

        qty = 1223
        Inventory.objects.create(inventorylocation=inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_product)

        leadtime_for_shipping_address.refresh_from_db()
        self.assertEqual(leadtime_for_shipping_address.leadtime, self.lead_time_overlap)

        inventory_qs = simple.inventory.filter_physical()
        locations = InventoryLocation.objects.filter(inventory__in=inventory_qs).values_list('id', flat=True)
        location_ids = list(locations.values_list('id', flat=True))
        location_ids_mtc = list(locations.values_list('multi_tenant_company', flat=True))
        self.assertEqual(location_ids_mtc, [inventory_location.multi_tenant_company.id])
        self.assertEqual(location_ids, [inventory_location.id])

        lead_time_product = LeadTime.objects.get_product_leadtime(simple)
        self.assertEqual(lead_time_product, leadtime_for_shipping_address.leadtime)
