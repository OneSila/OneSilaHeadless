from core.tests import TestCase, TestCaseDemoDataMixin
from inventory.models import InventoryLocation, Inventory
from products.models import SimpleProduct, SupplierProduct, BundleProduct, \
    DropshipProduct, ManufacturableProduct, BundleVariation
from .tests_models import InventoryTestCaseMixin
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU, SIMPLE_PEN_SKU
from shipments.flows import prepare_shipments_flow, pre_approve_shipping_flow


class TestInventoryNumbersTestCase(TestCaseDemoDataMixin, CreateTestOrderMixin, InventoryTestCaseMixin, TestCase):
    def pack_and_dispatch_all_items_in_order(self, order):
        from shipments.models import Package, PackageItem

        for shipment in order.shipment_set.all():
            package = Package.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Package.BOX,
                shipment=shipment)

            for item in shipment.shipmentitemtoship_set.all():
                physical_inventory = item.product.inventory.filter_physical().filter(quantity__gte=1)

                pre_physical = item.product.inventory.physical()

                package_item = package.packageitem_set.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product=item.product,
                    inventory=physical_inventory.first(),
                    quantity=item.quantity)

                post_physical = item.product.inventory.physical()

                self.assertFalse(post_physical == pre_physical)
                self.assertTrue(post_physical < pre_physical)

            package.set_status_dispatched()

    def test_inventory_number(self):
        # We start with a simple product with one supplier product and 10 items on stock
        # 1) We sell 1 - but leave the order on draft.
        #   So we should have 10 physically on stock, 0 reserved and 10 salable.
        # 2) When we change the status and mark it as processing, it should adjust the items to
        #   So we should have 10 physically on stock, 1 reserved and 9 salable.
        # 3) Ship the items, we still expect all the same items to be in the state before
        #   shipping
        # 4) Time for packing.  Pack and ship the items.
        #   items should be removed from physical and reserved stock

        simple = SimpleProduct.objects.get(multi_tenant_company=self.multi_tenant_company,
            sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU)

        pre_order_physical = simple.inventory.physical()
        pre_order_reserved = simple.inventory.reserved()
        pre_order_salable = simple.inventory.salable()

        order_qty = 1

        order = self.create_test_order('test_inventory_number', simple, order_qty)

        self.assertEqual(simple.inventory.physical(), pre_order_physical)
        self.assertEqual(simple.inventory.salable(), pre_order_salable)
        self.assertEqual(simple.inventory.reserved(), pre_order_reserved)

        # No need to take more action, the automated flows should just ship
        # these items without further action.
        order.set_status_pending_processing()
        self.assertEqual(order.status, order.SHIPPED)
        self.pack_and_dispatch_all_items_in_order(order)

        self.assertEqual(simple.inventory.physical(), pre_order_physical - order_qty)
        self.assertEqual(simple.inventory.reserved(), pre_order_reserved)
        self.assertEqual(simple.inventory.salable(), pre_order_salable - order_qty)

    def test_oversold_inventory_number(self):
        # We start with a simple product with one supplier product and 10 items on stock
        # 1) We sell 1 - but leave the order on draft.
        #   So we should have 10 physically on stock, 0 reserved and 10 salable.
        # 2) When we change the status and mark it as processing, it should adjust the items to
        #   So we should have 10 physically on stock, 1 reserved and 9 salable.

        simple = SimpleProduct.objects.get(multi_tenant_company=self.multi_tenant_company,
            sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        physical = simple.inventory.physical()
        reserved = simple.inventory.reserved()
        salable = simple.inventory.salable()

        order_qty = 100

        order = self.create_test_order('test_oversold_inventory_number', simple, order_qty)

        self.assertEqual(simple.inventory.physical(), physical)
        self.assertEqual(simple.inventory.salable(), salable)
        self.assertEqual(simple.inventory.reserved(), reserved)

        order.set_status_pending_processing()
        self.assertEqual(order.status, order.PENDING_SHIPPING_APPROVAL)

        self.assertEqual(simple.inventory.physical(), physical)
        self.assertEqual(simple.inventory.reserved(), reserved + order_qty)
        self.assertEqual(simple.inventory.salable(), 0)
        self.assertEqual(simple.inventory.await_inventory(), reserved + order_qty - physical)


class InventoryQuerySetPhysicalTestCase(InventoryTestCaseMixin, TestCase):
    def test_salable(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        qty = 321
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        simple.inventory.\
            order_by_least().\
            order_by_relevant_shippinglocation(self.inventory_location.shipping_address.country).\
            filter_internal().\
            filter_by_shippingaddress(self.inventory_location.shipping_address)

    def test_salable(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        qty = 321
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        salable = simple.inventory.salable()

        self.assertEqual(salable, qty)

    def test_salable_allow_backorder(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company, allow_backorder=True)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        qty = 321
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        salable = simple.inventory.salable()

        self.assertTrue(salable > qty)

    def test_reserved_zero(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        qty = 1223
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        reserved = simple.inventory.reserved()

        self.assertEqual(reserved, 0)

    def test_physical_simple_physical(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(simple)

        qty = 1223
        inventory = Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        inventory_ids = list(simple.inventory.filter_physical().values_list('id', flat=True))
        self.assertEqual(inventory_ids, [inventory.id])

        physical = simple.inventory.physical()
        self.assertEqual(physical, qty)

    def test_physical_dropship_physical(self):
        drop = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        supplier.base_products.add(drop)

        qty = 23325
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        physical = drop.inventory.physical()
        self.assertEqual(physical, qty)

    def test_physical_supplier_physical(self):
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        qty = 923
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        physical = supplier.inventory.physical()
        self.assertEqual(physical, qty)

    def test_physical_manufacturable_physical(self):
        manu = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        qty = 332
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=manu)

        physical = manu.inventory.physical()
        self.assertEqual(physical, qty)

    def test_physical_nested_bundles_with_simple(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        simple_one = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        simple_one.supplier_products.add(supplier_one)

        simple_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")
        simple_two.supplier_products.add(supplier_two)

        bundle_qty = 2
        BundleVariation.objects.create(parent=bundle, variation=simple_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=simple_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 100
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_one)

        qty_two = 20
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_two)

        physical = bundle.inventory.physical()
        self.assertEqual(physical, min(qty_one / bundle_qty, qty_two / bundle_qty))

        bundle.inventory.filter_physical()

    def test_physical_nested_bundles_with_bundle(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        bundle_one = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_one = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        simple_one.supplier_products.add(supplier_one)

        BundleVariation.objects.create(parent=bundle_one, variation=simple_one, quantity=1,
            multi_tenant_company=self.multi_tenant_company)

        bundle_two = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")
        simple_two.supplier_products.add(supplier_two)

        BundleVariation.objects.create(parent=bundle_two, variation=simple_two, quantity=1,
            multi_tenant_company=self.multi_tenant_company)

        bundle_qty = 2
        BundleVariation.objects.create(parent=bundle, variation=bundle_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=bundle_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 1420
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_one)

        qty_two = 12
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier_two)

        physical = bundle.inventory.physical()
        self.assertEqual(physical, min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_manufacturable(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        bundle_qty = 2
        BundleVariation.objects.create(parent=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 232
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=prod_one)

        qty_two = 2113
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=prod_two)

        physical = bundle.inventory.physical()
        self.assertEqual(physical, min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_dropship(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 3
        BundleVariation.objects.create(parent=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 44
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_one)

        qty_two = 111
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_two)

        expected = min(int(qty_one / bundle_qty), int(qty_two / bundle_qty))
        physical = bundle.inventory.physical()
        self.assertEqual(physical, expected)

    def test_physical_nested_bundles_with_simple_manufacturable(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 2
        BundleVariation.objects.create(parent=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 232
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=prod_one)

        qty_two = 2113
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_two)

        physical = bundle.inventory.physical()
        self.assertEqual(physical, min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_simple_dropship(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 3
        BundleVariation.objects.create(parent=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_two, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 2)

        qty_one = 44
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_one)

        qty_two = 111
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_two)

        expected = min(int(qty_one / bundle_qty), int(qty_two / bundle_qty))
        physical = bundle.inventory.physical()
        self.assertEqual(physical, expected)

    def test_physical_nested_bundles_with_simple_dropship_manufacturable_bundle(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_three = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-123")
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company, supplier=self.supplier, sku="SUP-1234")

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty_one = 3
        bundle_qty_two = 2
        bundle_qty_three = 1
        BundleVariation.objects.create(parent=bundle, variation=prod_one, quantity=bundle_qty_one,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_two, quantity=bundle_qty_two,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(parent=bundle, variation=prod_three, quantity=bundle_qty_three,
            multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(bundle.bundle_variations.all().count(), 3)

        qty_one = 44
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_one,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_one)

        qty_two = 111
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=sup_two)

        qty_three = 9233
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty_two,
            multi_tenant_company=self.multi_tenant_company,
            product=prod_three)

        expected = min(int(qty_one / bundle_qty_one), int(qty_two / bundle_qty_two), int(qty_three / bundle_qty_three))
        physical = bundle.inventory.physical()
        self.assertEqual(physical, expected)
