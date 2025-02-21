from contacts.models import Supplier, ShippingAddress
from core.signals import mutation_update, mutation_create
from core.tests import TestCase
from currencies.currencies import currencies
from currencies.models import Currency
from eancodes.models import EanCode
from eancodes.signals import ean_code_released_for_product
from inventory.models import Inventory, InventoryLocation
from products.models import ConfigurableProduct, SimpleProduct, BundleVariation, BundleProduct, ConfigurableVariation
from media.models import MediaProductThrough, Media
from products_inspector.constants import *
from products_inspector.models import Inspector
from django.core.files.uploadedfile import SimpleUploadedFile

from products_inspector.signals import inspector_missing_info_resolved, inspector_missing_info_detected
from properties.models import PropertySelectValue, Property, ProductProperty, PropertySelectValueTranslation, ProductPropertiesRule, ProductPropertiesRuleItem
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from units.models import Unit


class InspectorBlockHasImageTestCase(TestCase):
    def test_inspector_block_for_has_images(self):
        # Step 1: Create a configurable product (ConfigurableProduct)
        product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 2: Check that the inspector is created and has_missing_information is True
        inspector_block = product.inspector.blocks.get(error_code=HAS_IMAGES_ERROR)
        self.assertFalse(inspector_block.successfully_checked)

        # Step 3: Add a placeholder image to the product
        # Create a simple image file placeholder
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        media = Media.objects.create(
            type=Media.IMAGE,
            image=image,
            owner=self.user
        )

        MediaProductThrough.objects.create(
            product=product,
            media=media,
            sort_order=10,
            is_main_image=True,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 4: Refresh the inspector from the database
        inspector_block.refresh_from_db()

        # Step 5: Recheck the inspector's has_missing_information - it should now be False
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockMissingPricesTestCase(TestCase):

    def test_inspector_block_for_active_change(self):
        # Step 1: Create a required product (e.g., SimpleProduct)
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=False,  # Initially inactive
        )

        # Step 2: Check that the inspector block for MISSING_PRICES_ERROR is successfully checked (no error yet)
        inspector_block = product.inspector.blocks.get(error_code=MISSING_PRICES_ERROR)
        self.assertTrue(inspector_block.successfully_checked)

        # Step 3: Activate the product (now active and for sale without a price)
        product.active = True
        product.save()

        # Step 4: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 5: Recheck the inspector block's successfully_checked field - it should now be False (since no price exists)
        self.assertFalse(inspector_block.successfully_checked)


    def test_inspector_block_for_price_create_and_delete(self):
        # Step 1: Create a required product (e.g., SimpleProduct)
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Step 2: Check that the inspector block for MISSING_PRICES_ERROR is not successfully checked (price is missing)
        inspector_block = product.inspector.blocks.get(error_code=MISSING_PRICES_ERROR)
        self.assertFalse(inspector_block.successfully_checked)

        currency = Currency.objects.create(is_default_currency=True, multi_tenant_company=self.multi_tenant_company, **currencies['BE'])
        # Step 3: Add a SalesPrice to the product
        SalesPrice.objects.create(
            product=product,
            multi_tenant_company=self.multi_tenant_company,
            price=100.00,
            currency=currency
        )

        # Step 4: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 5: Recheck the inspector block's successfully_checked field - it should now be True (since price exists)
        self.assertTrue(inspector_block.successfully_checked)

        # Step 6: Remove the SalesPrice from the product
        SalesPrice.objects.filter(product=product).delete()

        # Step 7: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 8: Recheck the inspector block's successfully_checked field - it should now be False (since price is missing again)
        self.assertFalse(inspector_block.successfully_checked)


class InspectorBlockInactiveBundleItemsTest(TestCase):

    def test_inspector_block_for_inactive_bundle_item(self):
        # Step 1: Create a required product (e.g., BundleProduct)
        product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # The product is active
        )

        # Step 2: Create an active Bundle item (this should not trigger the error)
        active_item = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True
        )
        BundleVariation.objects.create(
            parent=product,
            variation=active_item,
            quantity=1.0,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 3: Refresh the inspector block from the database
        inspector_block = product.inspector.blocks.get(error_code=INACTIVE_BUNDLE_ITEMS_ERROR)
        inspector_block.refresh_from_db()

        # Step 4: Recheck the inspector block's successfully_checked field - it should be True
        self.assertTrue(inspector_block.successfully_checked)

        # Step 5: Create an inactive Bundle item (this should trigger the error)
        inactive_item = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=False  # The item is inactive
        )
        BundleVariation.objects.create(
            parent=product,
            variation=inactive_item,
            quantity=1.0,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 6: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 7: Recheck the inspector block's successfully_checked field - it should now be False
        self.assertFalse(inspector_block.successfully_checked)

    def test_inspector_block_for_bundle_item_activation(self):
        # Step 1: Create a required product (e.g., BundleProduct)
        product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # The product is active
        )

        # Step 2: Create an inactive Bundle item (this should trigger the error)
        inactive_item = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=False  # The item is inactive
        )
        BundleVariation.objects.create(
            parent=product,
            variation=inactive_item,
            quantity=1.0,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 3: Refresh the inspector block from the database
        inspector_block = product.inspector.blocks.get(error_code=INACTIVE_BUNDLE_ITEMS_ERROR)
        inspector_block.refresh_from_db()

        # Step 4: Recheck the inspector block's successfully_checked field - it should be False
        self.assertFalse(inspector_block.successfully_checked)

        # Step 5: Activate the Bundle item
        inactive_item.active = True
        inactive_item.save()

        # Step 6: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 7: Recheck the inspector block's successfully_checked field - it should now be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_bundle_item_creation_and_deletion(self):
        # Step 1: Create a required product (e.g., BundleProduct)
        product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # The product is active
        )

        # Step 2: Create an inactive Bundle item (this should trigger the error)
        inactive_item = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=False  # The item is inactive
        )
        bundle_variation = BundleVariation.objects.create(
            parent=product,
            variation=inactive_item,
            quantity=1.0,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 3: Refresh the inspector block from the database
        inspector_block = product.inspector.blocks.get(error_code=INACTIVE_BUNDLE_ITEMS_ERROR)
        inspector_block.refresh_from_db()

        # Step 4: Recheck the inspector block's successfully_checked field - it should be False
        self.assertFalse(inspector_block.successfully_checked)

        # Step 5: Remove the Bundle item
        bundle_variation.delete()

        # Step 6: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 7: Recheck the inspector block's successfully_checked field - it should now be True
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockMissingComponentsTest(TestCase):

    def test_inspector_block_for_missing_variation(self):
        # Step 1: Create a required product (e.g., ConfigurableProduct)
        product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # The product is active
        )

        # Step 2: Refresh the inspector block from the database
        inspector_block = product.inspector.blocks.get(error_code=MISSING_VARIATION_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be False (no variations)
        self.assertFalse(inspector_block.successfully_checked)

        # Step 4: Add a variation to the product
        variation = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True
        )
        ConfigurableVariation.objects.create(
            parent=product,
            variation=variation,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 5: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 6: Check the inspector block's successfully_checked field - it should now be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_missing_bundle_items(self):
        # Step 1: Create a required product (e.g., BundleProduct)
        product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # The product is active
        )

        # Step 2: Refresh the inspector block from the database
        inspector_block = product.inspector.blocks.get(error_code=MISSING_BUNDLE_ITEMS_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be False (no bundle items)
        self.assertFalse(inspector_block.successfully_checked)

        # Step 4: Add an item to the bundle
        bundle_item = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True
        )
        BundleVariation.objects.create(
            parent=product,
            variation=bundle_item,
            multi_tenant_company=self.multi_tenant_company
        )

        # Step 5: Refresh the inspector block from the database
        inspector_block.refresh_from_db()

        # Step 6: Check the inspector block's successfully_checked field - it should now be True
        self.assertTrue(inspector_block.successfully_checked)



class InspectorBlockMissingSupplierProductsTest(TestCase):

    def setUp(self):
        super().setUp()
        # Step 1: Set up a supplier, simple product, and a dropshipping product
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)
        self.simple_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,  # Product is active
        )


class InspectorBlockMissingEanCodeTest(TestCase):

    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.inherit_to_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.ean_code = "1234567890123"


    def test_inspector_block_for_ean_code_creation_with_product(self):
        # Step 1: Create an EAN code associated with the product
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code=self.ean_code
        )

        # Manually trigger the create mutation signal
        mutation_create.send(sender=self.product.__class__, instance=self.product)

        # Step 2: Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_EAN_CODE_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_ean_code_creation_with_inherit_to_product(self):
        # Step 1: Create an EAN code associated with the inherited product
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            inherit_to=self.inherit_to_product,
            ean_code=self.ean_code
        )

        # Manually trigger the create mutation signal
        mutation_create.send(sender=self.inherit_to_product.__class__, instance=self.inherit_to_product)

        # Step 2: Refresh the inspector block from the database
        inspector_block = self.inherit_to_product.inspector.blocks.get(error_code=MISSING_EAN_CODE_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_ean_code_update_with_product(self):
        # Step 1: Create an EAN code associated with the product
        ean_code_instance = EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code=self.ean_code
        )

        # Update the EAN code
        ean_code_instance.ean_code = "9876543210987"
        ean_code_instance.save()

        # Manually trigger the update mutation signal
        mutation_update.send(sender=ean_code_instance.__class__, instance=ean_code_instance)

        # Step 2: Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_EAN_CODE_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_ean_code_update_with_inherit_to_product(self):
        # Step 1: Create an EAN code associated with the inherited product
        ean_code_instance = EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            inherit_to=self.inherit_to_product,
            ean_code=self.ean_code
        )

        # Update the EAN code
        ean_code_instance.ean_code = "9876543210987"
        ean_code_instance.save()

        # Manually trigger the update mutation signal
        mutation_update.send(sender=ean_code_instance.__class__, instance=ean_code_instance)

        # Step 2: Refresh the inspector block from the database
        inspector_block = self.inherit_to_product.inspector.blocks.get(error_code=MISSING_EAN_CODE_ERROR)
        inspector_block.refresh_from_db()

        # Step 3: Check the inspector block's successfully_checked field - it should be True
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_for_ean_code_release(self):
        # Step 1: Create an EAN code associated with the product
        ean_code_instance = EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code=self.ean_code
        )

        ean_code_instance.product = None
        ean_code_instance.already_used = True
        ean_code_instance.save()

        # Manually trigger the mutation signal after releasing the EAN code
        ean_code_released_for_product.send(sender=self.product.__class__, instance=self.product)

        # Step 3: Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_EAN_CODE_ERROR)
        inspector_block.refresh_from_db()

        # Step 4: Check the inspector block's successfully_checked field - it should be False
        self.assertFalse(inspector_block.successfully_checked)


class InspectorBlockMissingProductTypeTest(TestCase):

    def setUp(self):
        super().setUp()

        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.product_tye, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_tye,
        )

        self.product_type_value_translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            value='Chair',
        )

        self.product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.product_tye,
            value_select=self.product_type_value
        )

    def test_inspector_block_missing_product_type_on_delete(self):
        # Remove the product type property and check the inspector block
        self.product_property.delete()

        # Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_PRODUCT_TYPE_ERROR)
        inspector_block.refresh_from_db()

        # Check the inspector block's successfully_checked field - it should be False
        self.assertFalse(inspector_block.successfully_checked)

    def test_inspector_block_with_product_type_present(self):
        # Inspector block should be successfully checked when a product type is present
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_PRODUCT_TYPE_ERROR)
        inspector_block.refresh_from_db()

        # The product has the required product type, so it should be successfully checked
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_on_update(self):
        # Test updating the product type property
        new_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_tye,
        )
        self.product_property.value_select = new_value
        self.product_property.save()

        # Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_PRODUCT_TYPE_ERROR)
        inspector_block.refresh_from_db()

        # Check the inspector block's successfully_checked field - it should still be True
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockMissingPropertiesTest(TestCase):

    def setUp(self):
        super().setUp()

        # Step 1: Set up the product
        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Step 2: Set up the product type property
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        self.product_type_value_translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            value='Table',
        )

        # Step 3: Create the ProductPropertiesRule for the product type
        self.product_properties_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        # Step 4: Create the required property (Color) and assign it to the rule
        self.color_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="color"
        )

        self.color_rule_itemm, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.product_properties_rule,
            property=self.color_property,
            type=ProductPropertiesRuleItem.REQUIRED
        )

        # Step 5: Create the optional property (Size) and assign it to the rule
        self.size_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="size"
        )

        self.size_rule_item, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.product_properties_rule,
            property=self.size_property,
            type=ProductPropertiesRuleItem.OPTIONAL
        )

        # Step 6: Assign product type to the product after the rule is created (for now)
        self.product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value
        )

    def test_inspector_block_missing_required_property(self):
        # This test will check if the product is missing the required property (Color)

        # At this point, the product should be missing the required Color property.
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_REQUIRED_PROPERTIES_ERROR)
        inspector_block.refresh_from_db()

        self.assertFalse(inspector_block.successfully_checked)

        # Now, add the required Color property to the product
        color_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.color_property,
        )

        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.color_property,
            value_select=color_value
        )

        # Refresh the inspector block
        inspector_block.refresh_from_db()

        # Now, the product should have the required Color property, so it should be successfully checked.
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_missing_optional_property(self):
        # This test will check if the product is missing the optional property (Size)

        # Initially, the inspector block should be successfully checked even if the Size property is missing,
        # because Size is optional.
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_OPTIONAL_PROPERTIES_ERROR)
        inspector_block.refresh_from_db()

        self.assertFalse(inspector_block.successfully_checked)

        # Now, add the optional Size property to the product
        size_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.size_property,
        )

        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.size_property,
            value_select=size_value
        )

        # Refresh the inspector block
        inspector_block.refresh_from_db()

        # The inspector block should remain successfully checked.
        self.assertTrue(inspector_block.successfully_checked)


# class InspectorBlockMissingStockTest(TestCase):
#
#     def setUp(self):
#         super().setUp()
#         self.simple_product = SimpleProduct.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             active=True,
#             allow_backorder=False
#         )
#
#         self.dropship_product = DropshipProduct.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             active=True,
#             allow_backorder=False
#         )
#
#         self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)
#         self.shipping_address = ShippingAddress.objects.create(multi_tenant_company=self.multi_tenant_company, company=self.supplier)
#         self.inventory_location, _ = InventoryLocation.objects.get_or_create(
#             shippingaddress=self.shipping_address,
#             name='InventoryTestCase',
#             multi_tenant_company=self.multi_tenant_company)
#
#
#     def test_inspector_block_missing_stock_with_no_backorder(self):
#         # Test missing stock with no backorder allowed for SimpleProduct
#
#         inspector_block = self.simple_product.inspector.blocks.get(error_code=MISSING_STOCK_ERROR)
#         inspector_block.refresh_from_db()
#
#         # The product has no stock, no backorder allowed, and is active and for sale
#         self.assertFalse(inspector_block.successfully_checked)
#
#         # Now, add stock to the product
#         self.supplier_inventory.quantity = 10
#         self.supplier_inventory.save()
#
#         # Refresh the inspector block after updating the stock
#         inspector_block.refresh_from_db()
#
#         self.assertTrue(inspector_block.successfully_checked)
#
#     def test_inspector_block_missing_stock_with_backorder_allowed(self):
#         # Test missing stock but with backorder allowed for DropshipProduct
#
#         # Update the product to allow backorder
#         self.dropship_product.allow_backorder = True
#         self.dropship_product.save()
#
#         inspector_block = self.dropship_product.inspector.blocks.get(error_code=MISSING_STOCK_ERROR)
#         inspector_block.refresh_from_db()
#
#         # The product allows backorder, so the inspector block should be successfully checked
#         self.assertTrue(inspector_block.successfully_checked)
#
#     def test_inspector_block_missing_stock_on_inventory_deletion(self):
#         # First, set some stock so the inspector block is successful
#         self.supplier_inventory.quantity = 10
#         self.supplier_inventory.save()
#
#         inspector_block = self.simple_product.inspector.blocks.get(error_code=MISSING_STOCK_ERROR)
#         inspector_block.refresh_from_db()
#
#         self.assertTrue(inspector_block.successfully_checked)
#
#         # Now delete the inventory and check the inspector block again
#         self.supplier_inventory.delete()
#
#         inspector_block.refresh_from_db()
#
#         # The product should now be flagged as missing stock
#         self.assertFalse(inspector_block.successfully_checked)

class InspectorBlockMissingManualPriceListOverrideTest(TestCase):

    def setUp(self):
        super().setUp()

        # Set up a product for testing
        self.product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.currency = Currency.objects.create(is_default_currency=True, multi_tenant_company=self.multi_tenant_company, **currencies['BE'])

        # Set up a SalesPriceList
        self.sales_price_list = SalesPriceList.objects.create(
            name="Test Price List",
            currency=self.currency,
            auto_update_prices=False,
            multi_tenant_company=self.multi_tenant_company
        )

        # Set up a SalesPriceListItem
        self.sales_price_list_item = SalesPriceListItem.objects.create(
            salespricelist=self.sales_price_list,
            product=self.product,
            price_auto=100,
            discount_auto=10,
            multi_tenant_company=self.multi_tenant_company
        )

    def test_inspector_block_missing_manual_pricelist_override_on_create_and_delete(self):
        # Ensure the inspector block fails when the price_override is null
        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR)
        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

        # Add a price_override and check if the block is successfully checked
        self.sales_price_list_item.price_override = 90
        self.sales_price_list_item.save()

        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Add a price_override and check if the block is successfully checked
        self.sales_price_list_item.price_override = None
        self.sales_price_list_item.save()

        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)
        # Remove the SalesPriceListItem and ensure the block fails again
        self.sales_price_list_item.delete()

        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

    def test_inspector_block_on_price_override_update(self):
        # Add a price_override and check if the block is successfully checked
        self.sales_price_list_item.price_override = 90
        self.sales_price_list_item.save()

        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR)
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Set price_override to null and check if the block fails
        self.sales_price_list_item.price_override = None
        self.sales_price_list_item.save()

        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

    def test_inspector_block_on_sales_pricelist_auto_update_change(self):
        # Change the SalesPriceList to auto-update prices and ensure the block is successfully checked
        self.sales_price_list.auto_update_prices = True
        self.sales_price_list.save()

        inspector_block = self.product.inspector.blocks.get(error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR)
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Change it back to manual update and ensure the block fails if price_override is null
        self.sales_price_list.auto_update_prices = False
        self.sales_price_list.save()

        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)


class InspectorBlockProductTypeMismatchTest(TestCase):

    def setUp(self):
        super().setUp()

        # Set up a common product type and two different select values
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type_value_1 = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        self.product_type_value_2 = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        # Set up a Configurable Product, Bundle Product, and Manufacturable Product for testing
        self.configurable_product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.bundle_product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Set up two simple products
        self.simple_product_1 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.simple_product_2 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

    def test_variation_mismatch_product_type(self):
        # Assign product type to configurable product
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.configurable_product,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )

        # Assign same product type to variations
        product_property_1 = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.simple_product_1,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )
        future_broken = product_property_2 = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.simple_product_2,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )

        # Link variations to configurable product
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.simple_product_1
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.simple_product_2
        )

        # Check if the inspector block is successfully checked
        inspector_block = self.configurable_product.inspector.blocks.get(error_code=VARIATION_MISMATCH_PRODUCT_TYPE_ERROR)
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        product_property_2.value_select = self.product_type_value_2
        product_property_2.save()

        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

        future_broken.delete()
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

    def test_items_mismatch_product_type(self):
        # Assign product type to bundle product
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.bundle_product,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )

        # Assign same product type to items
        product_property_1 = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.simple_product_1,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )
        product_property_2 = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.simple_product_2,
            property=self.product_type_property,
            value_select=self.product_type_value_1
        )

        # Link items to bundle product
        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.bundle_product,
            variation=self.simple_product_1
        )
        future_broken = BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.bundle_product,
            variation=self.simple_product_2
        )

        # Check if the inspector block is successfully checked
        inspector_block = self.bundle_product.inspector.blocks.get(error_code=ITEMS_MISMATCH_PRODUCT_TYPE_ERROR)
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Change one item's product type to a different value
        product_property_2.value_select = self.product_type_value_2
        product_property_2.save()

        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

        future_broken.delete()
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockMissingMandatoryInformationTest(TestCase):

    def setUp(self):
        super().setUp()

        # Set up the Simple Products, Configurable Product, Bundle Product, and Manufacturable Product
        self.simple_product_1 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.simple_product_2 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.configurable_product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.bundle_product = BundleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Link variations, items, and BOMs
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.simple_product_1
        )

        BundleVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.bundle_product,
            variation=self.simple_product_2
        )

    def test_variations_missing_mandatory_information(self):
        # Set has_missing_information to True for a variation and trigger the signal
        inspector = Inspector.objects.get(product=self.simple_product_1)
        inspector.has_missing_information = True
        inspector.save()

        inspector_missing_info_detected.send(sender=self.simple_product_1.__class__, instance=self.simple_product_1)

        # Check that the main inspector block for the configurable product fails
        inspector_block = self.configurable_product.inspector.blocks.get(error_code=VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR)
        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

        # Resolve the missing information and trigger the resolved signal
        inspector.has_missing_information = False
        inspector.save()
        inspector_missing_info_resolved.send(sender=self.simple_product_1.__class__, instance=self.simple_product_1)

        # Check that the main inspector block for the configurable product passes again
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Break it again, delete the variation, and check if it's fixed
        ConfigurableVariation.objects.filter(variation=self.simple_product_1).delete()
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

    def test_items_missing_mandatory_information(self):
        # Set has_missing_information to True for an item and trigger the signal
        inspector = Inspector.objects.get(product=self.simple_product_2)
        inspector.has_missing_information = True
        inspector.save()

        inspector_missing_info_detected.send(sender=self.simple_product_2.__class__, instance=self.simple_product_2)

        # Check that the main inspector block for the bundle product fails
        inspector_block = self.bundle_product.inspector.blocks.get(error_code=ITEMS_MISSING_MANDATORY_INFORMATION_ERROR)
        inspector_block.refresh_from_db()
        self.assertFalse(inspector_block.successfully_checked)

        # Resolve the missing information and trigger the resolved signal
        inspector.has_missing_information = False
        inspector.save()
        inspector_missing_info_resolved.send(sender=self.simple_product_2.__class__, instance=self.simple_product_2)

        # Check that the main inspector block for the bundle product passes again
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)

        # Break it again, delete the item, and check if it's fixed
        BundleVariation.objects.filter(variation=self.simple_product_2).delete()
        inspector_block.refresh_from_db()
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockNonConfigurableRuleTest(TestCase):

    def setUp(self):
        super().setUp()

        # Step 1: Set up the ConfigurableProduct
        self.product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Step 2: Set up the product type property
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        self.product_type_value_two = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        # Step 3: Create the first ProductPropertiesRule with REQUIRED color property
        self.first_product_properties_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.color_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="color"
        )

        self.first_color_rule_item, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.first_product_properties_rule,
            property=self.color_property,
            type=ProductPropertiesRuleItem.REQUIRED
        )

        # Step 4: Create the second ProductPropertiesRule with REQUIRED_IN_CONFIGURATOR color property
        self.second_product_properties_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value_two,
        )

        self.second_color_rule_item, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.second_product_properties_rule,
            property=self.color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
        )

        # Step 5: Assign product type to the product after the rule is created
        self.product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value
        )

    def test_non_configurable_rule_fails_with_required_rule(self):

        # Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=NON_CONFIGURABLE_RULE_ERROR)
        inspector_block.refresh_from_db()

        # The block should not be successfully checked because the product has a REQUIRED rule but no configurator rules
        self.assertFalse(inspector_block.successfully_checked)

    def test_non_configurable_rule_succeeds_with_configurator_rule(self):
        # Change the product property to the second rule (with REQUIRED_IN_CONFIGURATOR)
        self.product_property.value_select = self.product_type_value_two
        self.product_property.save()

        # Refresh the inspector block from the database
        inspector_block = self.product.inspector.blocks.get(error_code=NON_CONFIGURABLE_RULE_ERROR)
        inspector_block.refresh_from_db()

        # The block should be successfully checked because the product has the required configurator rules
        self.assertTrue(inspector_block.successfully_checked)


class InspectorBlockDuplicateVariationsTest(TestCase):

    def setUp(self):
        super().setUp()

        # Step 1: Set up the ConfigurableProduct
        self.configurable_product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Step 2: Set up the product type property
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )

        # Step 3: Create the ProductPropertiesRule with REQUIRED_IN_CONFIGURATOR color property
        self.product_properties_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.color_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name="color"
        )

        self.color_rule_item, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.product_properties_rule,
            property=self.color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
        )

        # Step 4: Assign product type to the ConfigurableProduct
        self.configurable_product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.configurable_product,
            property=self.product_type_property,
            value_select=self.product_type_value
        )

        # Step 5: Set up two SimpleProducts as variations of the ConfigurableProduct
        self.variation1 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        self.variation2 = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

        # Step 6: Assign the same product type to the variations
        self.variation1_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.variation1,
            property=self.product_type_property,
            value_select=self.product_type_value
        )

        self.variation2_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.variation2,
            property=self.product_type_property,
            value_select=self.product_type_value
        )

        # Step 7: Add both variations to the ConfigurableProduct's parent
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.variation1
        )

        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.variation2
        )

        # Step 8: Set the color of both variations to Red
        self.red_color_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.color_property
        )

        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.variation1,
            property=self.color_property,
            value_select=self.red_color_value
        )

        self.variation2_color_value = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.variation2,
            property=self.color_property,
            value_select=self.red_color_value
        )

    def test_duplicate_variations_should_fail(self):
        # Trigger the inspector block refresh to simulate the check

        # Refresh the inspector block from the database
        inspector_block = self.configurable_product.inspector.blocks.get(error_code=DUPLICATE_VARIATIONS_ERROR)
        inspector_block.refresh_from_db()

        # Since both variations have the same color, the inspector block should fail
        self.assertFalse(inspector_block.successfully_checked)

    def test_duplicate_variations_should_succeed_after_change(self):
        # Change the color of the second variation to Blue
        blue_color_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.color_property
        )

        self.variation2_color_value.value_select = blue_color_value
        self.variation2_color_value.save()

        # Refresh the inspector block from the database
        inspector_block = self.configurable_product.inspector.blocks.get(error_code=DUPLICATE_VARIATIONS_ERROR)
        inspector_block.refresh_from_db()

        # The inspector block should now pass since the variations have different colors
        self.assertTrue(inspector_block.successfully_checked)

    def test_duplicate_variations_should_succeed_after_deletion(self):
        # Delete one of the variations
        self.variation2.delete()

        # Refresh the inspector block from the database
        inspector_block = self.configurable_product.inspector.blocks.get(error_code=DUPLICATE_VARIATIONS_ERROR)
        inspector_block.refresh_from_db()

        # The inspector block should now pass since there is only one variation left
        self.assertTrue(inspector_block.successfully_checked)
