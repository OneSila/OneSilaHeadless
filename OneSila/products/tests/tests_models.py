from django.db import IntegrityError

from contacts.models import Supplier
from core.tests import TestCase
from products.models import SupplierProduct, ConfigurableProduct, \
    SimpleProduct, BundleProduct, DropshipProduct, ManufacturableProduct, \
    BundleVariation

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

    def test_get_parent_products_in_depth(self):
        # A supplier product is expected to retun itself.
        supplier = Supplier.objects.create(multi_tenant_company=self.multi_tenant_company)
        supplier_product = SupplierProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku='test-1929',
            supplier=supplier)
        self.assertTrue(supplier_product.id in supplier_product.get_parent_products(ids_only=True))

        # A supplier with parent simple is expected to return the
        # simple(s)
        simple_product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_product.supplier_products.add(supplier_product)
        self.assertTrue(supplier_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(simple_product.id in supplier_product.get_parent_products(ids_only=True))

        # A supplier with dropship bundle is expected to return the
        # simple(s)
        dropship_product = DropshipProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        dropship_product.supplier_products.add(supplier_product)
        self.assertTrue(supplier_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(simple_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(dropship_product.id in supplier_product.get_parent_products(ids_only=True))

        # A simple with bundle parent is supposed to return the bundle(s)
        bundle_product = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=bundle_product,
            variation=simple_product,
            quantity=1
        )
        self.assertTrue(supplier_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(simple_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(dropship_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in simple_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in bundle_product.get_parent_products(ids_only=True))

        # Manufacturable product is expected to return the manufacturable
        # product
        manufacturable_product = ManufacturableProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=bundle_product,
            variation=manufacturable_product,
            quantity=1
        )
        self.assertTrue(manufacturable_product.id in manufacturable_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in manufacturable_product.get_parent_products(ids_only=True))

        # A bundle in a bundle is expected to return the higher bundle
        bundle_product_two = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=bundle_product_two,
            variation=bundle_product,
            quantity=1)
        self.assertTrue(bundle_product_two.id in supplier_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in bundle_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product_two.id in bundle_product.get_parent_products(ids_only=True))
