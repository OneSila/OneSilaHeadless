from django.db import IntegrityError

from contacts.models import Supplier
from core.tests import TestCase
from products.models import SupplierProduct, ConfigurableProduct, SimpleProduct, BundleProduct, DropshipProduct, ManufacturableProduct

# class ProductIntegrityTestCase(TestCase):
#     def test_supplier_on_bundle_product(self):
#         prod = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
#         sup = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

#         with self.assertRaises(IntegrityError):
#             prod.bundle_variations.add(sup)


class ProductModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)

    def test_supplier_product_requires_both_sku_and_supplier(self):
        with self.assertRaises(IntegrityError):
            SupplierProduct.objects.create(
                multi_tenant_company=self.multi_tenant_company
            )

    def test_supplier_product_requires_supplier(self):
        with self.assertRaises(IntegrityError):
            SupplierProduct.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sku="SUP-12345"
            )

    def test_supplier_product_requires_sku(self):
        with self.assertRaises(IntegrityError):
            SupplierProduct.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                supplier=self.supplier,
            )

    def test_supplier_product_creation(self):
        supplier_product = SupplierProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SUP-12345",
            supplier=self.supplier
        )
        self.assertEqual(supplier_product.sku, "SUP-12345")

    def test_other_product_types_without_supplier_and_sku(self):
        # Should allow creating without supplier and sku
        configurable_product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(configurable_product.sku)

        simple_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(simple_product.sku)

        bundle_product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(bundle_product.sku)

        dropship_product = DropshipProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(dropship_product.sku)

        manufacturable_product = ManufacturableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(manufacturable_product.sku)
