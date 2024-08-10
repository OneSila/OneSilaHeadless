from core.tests import TestCase, TestWithDemoDataMixin
from contacts.models import ShippingAddress, Supplier
from inventory.models import InventoryLocation, Inventory
from products.models import SimpleProduct, SupplierProduct, BundleProduct, \
    BundleVariation
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
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)
        self.shipping_address = ShippingAddress.objects.create(multi_tenant_company=self.multi_tenant_company, company=self.supplier)

    def test_filter_fastest(self):
        filtered = LeadTime.objects.\
            filter_fastest([self.lead_time_fast.id, self.lead_time_overlap.id, self.lead_time_slow.id])

        self.assertEqual(filtered, self.lead_time_fast)

    def test_filter_fastest_qs(self):
        filtered = LeadTime.objects.filter(multi_tenant_company=self.multi_tenant_company)
        fastest = filtered.filter_fastest()

        self.assertEqual(fastest, self.lead_time_fast)

    def test_leadtime_for_outofstock_product(self):
        product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
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
            supplier=supplier, sku="SUP-123")
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

    def test_lead_time_for_bundle_and_simples(self):
        # Base setup first product
        supplier = Supplier.objects.filter(multi_tenant_company=self.multi_tenant_company).first()
        shippingaddress = ShippingAddress.objects.filter(
            company=supplier,
            multi_tenant_company=self.multi_tenant_company).last()

        inventory_location, _ = InventoryLocation.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            name='for_inv_bundle_one', shippingaddress=shippingaddress)
        leadtime_for_shipping_address, _ = LeadTimeForShippingAddress.objects.get_or_create(shippingaddress=shippingaddress,
            multi_tenant_company=self.multi_tenant_company)

        leadtime_for_shipping_address.leadtime = self.lead_time_overlap
        leadtime_for_shipping_address.save()

        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company,
            supplier=supplier, sku="SUP-123")
        supplier_product.base_products.add(simple)

        qty = 1223
        Inventory.objects.create(inventorylocation=inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_product)

        simple_leadtime = LeadTime.objects.get_product_leadtime(simple)
        self.assertEqual(simple_leadtime, self.lead_time_overlap)

        # Second simple product
        supplier_two = Supplier.objects.filter(multi_tenant_company=self.multi_tenant_company).last()
        self.assertFalse(supplier_two == supplier)

        shippingaddress_two = ShippingAddress.objects.filter(
            company=supplier_two,
            multi_tenant_company=self.multi_tenant_company).first()
        self.assertFalse(shippingaddress == shippingaddress_two)

        inventory_location_two, _ = InventoryLocation.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            name='for_inv_bundle_two', shippingaddress=shippingaddress_two)
        leadtime_for_shipping_address_two, _ = LeadTimeForShippingAddress.objects.get_or_create(
            shippingaddress=shippingaddress_two,
            multi_tenant_company=self.multi_tenant_company)

        leadtime_for_shipping_address_two.leadtime = self.lead_time_slow
        leadtime_for_shipping_address_two.save()

        simple_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_product_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company,
            supplier=supplier_two, sku="SUP-123-BIS")
        supplier_product_two.base_products.add(simple_two)

        # We force the _two items to be used by setting a lower qty
        qty = 123
        Inventory.objects.create(inventorylocation=inventory_location_two,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_product_two)

        simple_two_leadtime = LeadTime.objects.get_product_leadtime(simple_two)
        self.assertEqual(simple_two_leadtime, self.lead_time_slow)

        # Now the final piece, add the bundle items.
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=simple, multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=simple_two, multi_tenant_company=self.multi_tenant_company)

        bundle_leadtime = LeadTime.objects.get_product_leadtime(bundle)

        self.assertEqual(bundle_leadtime, self.lead_time_slow)
