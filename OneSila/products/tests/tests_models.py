from django.db import IntegrityError

from contacts.models import Supplier
from core.tests import TestCase
from products.models import (
    ConfigurableProduct,
    SimpleProduct,
    BundleProduct,
    BundleVariation,
    AliasProduct,
    ProductTranslation,
)
from media.models import Media, MediaProductThrough
from properties.models import Property, PropertyTranslation, ProductProperty, ProductPropertyTextTranslation
from sales_prices.models import SalesPrice


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


class DuplicateProductTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Original",
            multi_tenant_company=self.multi_tenant_company,
        )

        media = Media.objects.create(type=Media.IMAGE, multi_tenant_company=self.multi_tenant_company)
        MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            multi_tenant_company=self.multi_tenant_company,
        )

        prop = Property.objects.create(type=Property.TYPES.TEXT, multi_tenant_company=self.multi_tenant_company)
        PropertyTranslation.objects.create(
            property=prop,
            language=self.multi_tenant_company.language,
            name="Prop",
            multi_tenant_company=self.multi_tenant_company,
        )
        pp = ProductProperty.objects.create(
            product=self.product,
            property=prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            product_property=pp,
            language=self.multi_tenant_company.language,
            value_text="Value",
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=10,
            price=8,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_duplicate_product_manager(self):
        duplicate = SimpleProduct.objects.duplicate_product(self.product)
        self.assertNotEqual(duplicate.id, self.product.id)
        self.assertEqual(duplicate.translations.count(), self.product.translations.count())
        self.assertEqual(duplicate.mediaproductthrough_set.count(), self.product.mediaproductthrough_set.count())
        self.assertEqual(duplicate.productproperty_set.count(), self.product.productproperty_set.count())
        self.assertEqual(duplicate.salesprice_set.count(), self.product.salesprice_set.count())

    def test_duplicate_product_existing_sku_error(self):
        with self.assertRaises(Exception):
            SimpleProduct.objects.duplicate_product(self.product, sku=self.product.sku)
