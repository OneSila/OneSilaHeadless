from django.db import IntegrityError

from contacts.models import Supplier
from core.tests import TestCase
from products.models import (
    ConfigurableProduct,
    SimpleProduct,
    BundleProduct,
    BundleVariation,
    ConfigurableVariation,
    AliasProduct,
    ProductTranslation,
    Product,
    ProductTranslationBulletPoint,
)
from media.models import Media, MediaProductThrough
from properties.models import Property, PropertyTranslation, ProductProperty, ProductPropertyTextTranslation
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import SalesChannelIntegrationPricelist


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

    def test_alias_product_cannot_be_its_own_parent(self):
        simple_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )

        alias_product = AliasProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            alias_parent_product=simple_product
        )

        alias_product.alias_parent_product = alias_product

        with self.assertRaisesMessage(
            ValueError,
            "An alias product cannot point to another alias product.",
        ):
            alias_product.save()

    def test_copy_from_parent_copies_default_translations(self):
        parent = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        translation = ProductTranslation.objects.create(
            product=parent,
            language=self.multi_tenant_company.language,
            name="Parent name",
            short_description="Parent short",
            description="Parent description",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=translation,
            text="First",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

        alias = AliasProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            alias_parent_product=parent,
        )

        AliasProduct.objects.copy_from_parent(alias)

        alias_translation = alias.translations.get(
            language=self.multi_tenant_company.language,
            sales_channel=None,
        )
        self.assertEqual(alias_translation.name, "Parent name")
        self.assertEqual(alias_translation.short_description, "Parent short")
        self.assertEqual(alias_translation.description, "Parent description")
        self.assertEqual(alias_translation.bullet_points.count(), 1)
        self.assertEqual(
            alias_translation.bullet_points.first().text,
            "First",
        )

    def test_copy_from_parent_skips_content_when_disabled(self):
        parent = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        ProductTranslation.objects.create(
            product=parent,
            language=self.multi_tenant_company.language,
            name="Parent name",
            multi_tenant_company=self.multi_tenant_company,
        )

        alias = AliasProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            alias_parent_product=parent,
        )

        AliasProduct.objects.copy_from_parent(alias, copy_content=False)

        self.assertFalse(
            alias.translations.filter(
                language=self.multi_tenant_company.language,
                sales_channel=None,
            ).exists()
        )


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

    def test_explicit_sku_is_trimmed(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="  CUSTOM-SKU  ",
        )
        product.refresh_from_db()
        self.assertEqual(product.sku, "CUSTOM-SKU")

    def test_whitespace_only_sku_generates_new_value(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="   ",
        )
        product.refresh_from_db()
        self.assertTrue(product.sku)
        self.assertEqual(product.sku, product.sku.strip())


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

    def _create_relationships(self):
        configurable_parent = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        ConfigurableVariation.objects.create(
            parent=configurable_parent,
            variation=self.product,
            multi_tenant_company=self.multi_tenant_company,
        )

        bundle_parent = BundleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        BundleVariation.objects.create(
            parent=bundle_parent,
            variation=self.product,
            quantity=1,
            multi_tenant_company=self.multi_tenant_company,
        )

        return configurable_parent, bundle_parent

    def test_duplicate_product_manager(self):
        duplicate = SimpleProduct.objects.duplicate_product(self.product)
        self.assertNotEqual(duplicate.id, self.product.id)
        self.assertEqual(duplicate.translations.count(), self.product.translations.count())
        self.assertEqual(duplicate.mediaproductthrough_set.count(), self.product.mediaproductthrough_set.count())
        self.assertEqual(duplicate.productproperty_set.count(), self.product.productproperty_set.count())
        self.assertEqual(duplicate.salesprice_set.count(), self.product.salesprice_set.count())

    def test_duplicate_product_copies_relationships_by_default(self):
        configurable_parent, bundle_parent = self._create_relationships()

        duplicate = SimpleProduct.objects.duplicate_product(self.product)

        self.assertTrue(
            ConfigurableVariation.objects.filter(
                parent=configurable_parent,
                variation=duplicate,
            ).exists()
        )
        self.assertTrue(
            BundleVariation.objects.filter(
                parent=bundle_parent,
                variation=duplicate,
            ).exists()
        )

    def test_duplicate_product_existing_sku_error(self):
        with self.assertRaises(Exception):
            SimpleProduct.objects.duplicate_product(self.product, sku=self.product.sku)

    def test_duplicate_product_manager_as_alias(self):
        duplicate = SimpleProduct.objects.duplicate_product(
            self.product, create_as_alias=True
        )
        self.assertEqual(duplicate.type, Product.ALIAS)
        self.assertEqual(duplicate.alias_parent_product, self.product)

    def test_duplicate_product_skips_relationships_when_disabled(self):
        configurable_parent, bundle_parent = self._create_relationships()

        duplicate = SimpleProduct.objects.duplicate_product(
            self.product,
            create_relationships=False,
        )

        self.assertFalse(
            ConfigurableVariation.objects.filter(
                parent=configurable_parent,
                variation=duplicate,
            ).exists()
        )
        self.assertFalse(
            BundleVariation.objects.filter(
                parent=bundle_parent,
                variation=duplicate,
            ).exists()
        )


class ProductTranslationModelTest(TestCase):
    def test_duplicate_default_translation_not_allowed(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ProductTranslation.objects.create(
            product=product,
            language=self.multi_tenant_company.language,
            name="Original",
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(IntegrityError):
            ProductTranslation.objects.create(
                product=product,
                language=self.multi_tenant_company.language,
                name="Duplicate",
                multi_tenant_company=self.multi_tenant_company,
            )


class ProductPriceValidationTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )
        self.price_list = SalesPriceList.objects.create(
            name="pl",
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=self.price_list,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _create_item(self, price, discount):
        return SalesPriceListItem.objects.create(
            salespricelist=self.price_list,
            product=self.product,
            price_override=price,
            discount_override=discount,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_discount_greater_or_equal_returns_full_price_only(self):
        self._create_item(100, 120)
        full_price, discount = self.product.get_price_for_sales_channel(
            self.channel, self.currency
        )
        self.assertEqual(full_price, 100)
        self.assertIsNone(discount)

    def test_zero_price_raises_error(self):
        SalesPriceListItem.objects.create(
            salespricelist=self.price_list,
            product=self.product,
            price_auto=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        with self.assertRaises(ValueError):
            self.product.get_price_for_sales_channel(self.channel, self.currency)

    def test_zero_discount_raises_error(self):
        SalesPriceListItem.objects.create(
            salespricelist=self.price_list,
            product=self.product,
            price_override=100,
            discount_auto=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        with self.assertRaises(ValueError):
            self.product.get_price_for_sales_channel(self.channel, self.currency)
