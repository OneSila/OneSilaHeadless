from core.tests import TestCase
from django.db import IntegrityError
from inventory.models import Inventory, InventoryLocation
from products.models import SupplierProduct, UmbrellaProduct, \
    SimpleProduct, BundleProduct, DropshipProduct, ManufacturableProduct


class InventoryTestCaseMixin:
    def setUp(self):
        super().setUp()
        self.inventory_location, _ = InventoryLocation.objects.get_or_create(
            name='InventoryTestCase',
            multi_tenant_company=self.multi_tenant_company)


class InventoryTestCase(InventoryTestCaseMixin, TestCase):
    def test_inventory_on_configurable_product(self):
        prod = UmbrellaProduct.objects.create(
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
        self.assertEqual(prod.inventory.physical(), quantity)

    def test_inventory_on_simple_product(self):
        prod = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company)

        with self.assertRaises(IntegrityError):
            Inventory.objects.create(product=prod,
                inventorylocation=self.inventory_location,
                multi_tenant_company=self.multi_tenant_company,
                quantity=10)
