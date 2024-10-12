from contacts.models import Supplier, ShippingAddress
from core.tests import TestCase, TestCaseDemoDataMixin
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from inventory.models import Inventory, InventoryLocation, InventoryMovement
from products.models import SupplierProduct, ConfigurableProduct, Product, \
    SimpleProduct, BundleProduct, DropshipProduct, ManufacturableProduct
from products.demo_data import SIMPLE_BLACK_FABRIC_NAME


class InventoryTestCaseMixin:
    def setUp(self):
        super().setUp()
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)
        self.shipping_address = ShippingAddress.objects.create(multi_tenant_company=self.multi_tenant_company, company=self.supplier)
        self.inventory_location, _ = InventoryLocation.objects.get_or_create(
            shippingaddress=self.shipping_address,
            name='InventoryTestCase',
            multi_tenant_company=self.multi_tenant_company)
        self.inventory_location_bis, _ = InventoryLocation.objects.get_or_create(
            shippingaddress=self.shipping_address,
            name='InventoryTestCaseBis',
            multi_tenant_company=self.multi_tenant_company)


class InventoryTestCase(TestCaseDemoDataMixin, InventoryTestCaseMixin, TestCase):
    def test_reductions(self):
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=0)
        inv.increase_quantity(quantity)
        self.assertEqual(inv.quantity, quantity)

        inv.reduce_quantity(quantity)
        self.assertEqual(inv.quantity, 0)

        loc = self.inventory_location
        loc.increase_quantity(prod, quantity)
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, quantity)
        loc.reduce_quantity(prod, quantity)
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 0)

    def test_inventory_reduce_too_much(self):
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=quantity)

        with self.assertRaises(IntegrityError):
            inv.reduce_quantity(quantity + 1)

    def test_inventory_to_inventory_not_identical(self):
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=quantity)
        inv_qty_ori = inv.quantity

        with self.assertRaises(ValidationError):
            InventoryMovement.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                movement_from=inv,
                movement_to=inv,
                quantity=quantity,
                product=prod)

    def test_inventory_to_inventory_movement(self):
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=quantity)
        inv_qty_ori = inv.quantity

        inv_bis = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location_bis,
                multi_tenant_company=self.multi_tenant_company,
                quantity=0)
        inv_qty_bis_ori = inv_bis.quantity

        movement = InventoryMovement.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            movement_from=self.inventory_location,
            movement_to=self.inventory_location_bis,
            quantity=quantity,
            product=prod)

        inv.refresh_from_db()
        inv_bis.refresh_from_db()

        self.assertEqual(inv_qty_ori - quantity, inv.quantity)
        self.assertEqual(inv_qty_bis_ori + quantity, inv_bis.quantity)

    def test_inventory_on_configurable_product(self):
        prod = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10

        with self.assertRaises(IntegrityError):
            inv = Inventory.objects.create(product=prod,
                    inventorylocation=self.inventory_location,
                    multi_tenant_company=self.multi_tenant_company,
                    quantity=quantity)

    def test_inventory_on_manufacturable_product(self):
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=quantity)
        physical = prod.inventory.physical()
        self.assertEqual(physical, quantity)

    def test_inventory_on_simple_product(self):
        prod = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)

        with self.assertRaises(IntegrityError):
            Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=10)

    def test_find_inventory_shippingaddresses(self):
        from contacts.models import ShippingAddress
        prod = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)
        quantity = 10
        inv = Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=quantity)

        qs = prod.inventory.find_inventory_shippingaddresses()
        self.assertTrue(qs.exists())
        address = qs.first()
        self.assertTrue(isinstance(address, ShippingAddress))
        self.assertTrue(address == self.shipping_address)
