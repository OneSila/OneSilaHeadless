from django.db import IntegrityError

from contacts.models import Supplier
from core.tests import TestCase
from products.models import ConfigurableProduct, \
    SimpleProduct, BundleProduct, BundleVariation, \
    AliasProduct


class AlasProductTestCase(TestCase):
    def test_alias_product_constraint(self):
        simple_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.assertIsNotNone(simple_product.sku)

        alias_product = AliasProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            alias_parent_product=simple_product
        )
        self.assertIsNotNone(alias_product.sku)


class ProductModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)

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

    def test_get_parent_products_in_depth(self):
        # A supplier product is expected to retun itself.
        # A supplier with parent simple is expected to return the
        # simple(s)
        simple_product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        # A simple with bundle parent is supposed to return the bundle(s)
        bundle_product = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=bundle_product,
            variation=simple_product,
            quantity=1
        )
        self.assertTrue(bundle_product.id in simple_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product.id in bundle_product.get_parent_products(ids_only=True))

        # A bundle in a bundle is expected to return the higher bundle
        bundle_product_two = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=bundle_product_two,
            variation=bundle_product,
            quantity=1)
        self.assertTrue(bundle_product.id in bundle_product.get_parent_products(ids_only=True))
        self.assertTrue(bundle_product_two.id in bundle_product.get_parent_products(ids_only=True))
