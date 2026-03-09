from core.tests import TestCase
from products.models import ConfigurableVariation, Product

from sales_channels.integrations.ebay.models import (
    EbayProductStoreCategory,
    EbaySalesChannel,
    EbayStoreCategory,
)


class EbayProductStoreCategoryPropagationReceiverTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://ebay.receiver.test",
            active=True,
        )
        self.parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="PARENT-SKU",
        )
        self.child_one = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CHILD-1",
        )
        self.child_two = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CHILD-2",
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.parent_product,
            variation=self.child_one,
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.parent_product,
            variation=self.child_two,
        )

    def _create_store_category(self, *, remote_id: str, name: str, parent=None, level: int = 1, is_leaf: bool = False):
        return EbayStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            name=name,
            parent=parent,
            order=0,
            level=level,
            is_leaf=is_leaf,
        )

    def test_create_propagates_to_all_variations(self):
        fashion = self._create_store_category(remote_id="10", name="Fashion", level=1, is_leaf=False)
        shirts = self._create_store_category(
            remote_id="11",
            name="Shirts",
            parent=fashion,
            level=2,
            is_leaf=True,
        )

        EbayProductStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.parent_product,
            primary_store_category=shirts,
        )

        self.assertTrue(
            EbayProductStoreCategory.objects.filter(
                product=self.child_one,
                primary_store_category=shirts,
                secondary_store_category__isnull=True,
            ).exists()
        )
        self.assertTrue(
            EbayProductStoreCategory.objects.filter(
                product=self.child_two,
                primary_store_category=shirts,
                secondary_store_category__isnull=True,
            ).exists()
        )

    def test_update_propagates_and_replaces_old_value(self):
        fashion = self._create_store_category(remote_id="20", name="Fashion", level=1, is_leaf=False)
        shirts = self._create_store_category(
            remote_id="21",
            name="Shirts",
            parent=fashion,
            level=2,
            is_leaf=True,
        )
        accessories = self._create_store_category(
            remote_id="22",
            name="Accessories",
            parent=fashion,
            level=2,
            is_leaf=True,
        )

        assignment = EbayProductStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.parent_product,
            primary_store_category=shirts,
        )
        assignment.primary_store_category = accessories
        assignment.save(update_fields=["primary_store_category"])

        self.assertFalse(
            EbayProductStoreCategory.objects.filter(
                product=self.child_one,
                primary_store_category=shirts,
            ).exists()
        )
        self.assertTrue(
            EbayProductStoreCategory.objects.filter(
                product=self.child_one,
                primary_store_category=accessories,
                secondary_store_category__isnull=True,
            ).exists()
        )
        self.assertTrue(
            EbayProductStoreCategory.objects.filter(
                product=self.child_two,
                primary_store_category=accessories,
                secondary_store_category__isnull=True,
            ).exists()
        )

    def test_delete_propagates_to_all_variations(self):
        fashion = self._create_store_category(remote_id="30", name="Fashion", level=1, is_leaf=False)
        shirts = self._create_store_category(
            remote_id="31",
            name="Shirts",
            parent=fashion,
            level=2,
            is_leaf=True,
        )

        assignment = EbayProductStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.parent_product,
            primary_store_category=shirts,
        )
        self.assertTrue(EbayProductStoreCategory.objects.filter(product=self.child_one).exists())
        self.assertTrue(EbayProductStoreCategory.objects.filter(product=self.child_two).exists())

        assignment.delete()

        self.assertFalse(EbayProductStoreCategory.objects.filter(product=self.child_one).exists())
        self.assertFalse(EbayProductStoreCategory.objects.filter(product=self.child_two).exists())
