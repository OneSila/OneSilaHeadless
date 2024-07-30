from core.tests import TestCase
from inventory.models import InventoryLocation, Inventory
from products.models import SimpleProduct, SupplierProduct, BundleProduct, \
    DropshipProduct, UmbrellaProduct, ManufacturableProduct, BundleVariation
from .tests_models import InventoryTestCaseMixin


class InventoryQuerySetPhysicalTestCase(InventoryTestCaseMixin, TestCase):
    def test_reserved_zero(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier.base_products.add(simple)

        qty = 1223
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        self.assertEqual(simple.inventory.reserved(), 0)

    def test_physical_simple_physical(self):
        simple = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier.base_products.add(simple)

        qty = 1223
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        self.assertEqual(simple.inventory.physical(), qty)

    def test_physical_dropship_physical(self):
        drop = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier.base_products.add(drop)

        qty = 23325
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        self.assertEqual(drop.inventory.physical(), qty)

    def test_physical_supplier_physical(self):
        supplier = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        qty = 923
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=supplier)

        self.assertEqual(supplier.inventory.physical(), qty)

    def test_physical_manufacturable_physical(self):
        manu = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        qty = 332
        Inventory.objects.create(inventorylocation=self.inventory_location,
            quantity=qty,
            multi_tenant_company=self.multi_tenant_company,
            product=manu)

        self.assertEqual(manu.inventory.physical(), qty)

    def test_physical_nested_bundles_with_simple(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        simple_one = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_one.supplier_products.add(supplier_one)

        simple_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_two.supplier_products.add(supplier_two)

        bundle_qty = 2
        BundleVariation.objects.create(umbrella=bundle, variation=simple_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=simple_two, quantity=bundle_qty,
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

        self.assertEqual(bundle.inventory.physical(), min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_bundle(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        bundle_one = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_one = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_one.supplier_products.add(supplier_one)

        BundleVariation.objects.create(umbrella=bundle_one, variation=simple_one, quantity=1,
            multi_tenant_company=self.multi_tenant_company)

        bundle_two = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_two.supplier_products.add(supplier_two)

        BundleVariation.objects.create(umbrella=bundle_two, variation=simple_two, quantity=1,
            multi_tenant_company=self.multi_tenant_company)

        bundle_qty = 2
        BundleVariation.objects.create(umbrella=bundle, variation=bundle_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=bundle_two, quantity=bundle_qty,
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

        self.assertEqual(bundle.inventory.physical(), min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_manufacturable(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        bundle_qty = 2
        BundleVariation.objects.create(umbrella=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_two, quantity=bundle_qty,
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

        self.assertEqual(bundle.inventory.physical(), min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_dropship(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 3
        BundleVariation.objects.create(umbrella=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_two, quantity=bundle_qty,
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
        self.assertEqual(bundle.inventory.physical(), expected)

    def test_physical_nested_bundles_with_simple_manufacturable(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 2
        BundleVariation.objects.create(umbrella=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_two, quantity=bundle_qty,
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

        self.assertEqual(bundle.inventory.physical(), min(qty_one / bundle_qty, qty_two / bundle_qty))

    def test_physical_nested_bundles_with_simple_dropship(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty = 3
        BundleVariation.objects.create(umbrella=bundle, variation=prod_one, quantity=bundle_qty,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_two, quantity=bundle_qty,
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
        self.assertEqual(bundle.inventory.physical(), expected)

    def test_physical_nested_bundles_with_simple_dropship_manufacturable_bundle(self):
        bundle = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        prod_three = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        sup_one = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        sup_two = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        prod_one.supplier_products.add(sup_one)
        prod_two.supplier_products.add(sup_two)

        bundle_qty_one = 3
        bundle_qty_two = 2
        bundle_qty_three = 1
        BundleVariation.objects.create(umbrella=bundle, variation=prod_one, quantity=bundle_qty_one,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_two, quantity=bundle_qty_two,
            multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(umbrella=bundle, variation=prod_three, quantity=bundle_qty_three,
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
        self.assertEqual(bundle.inventory.physical(), expected)
