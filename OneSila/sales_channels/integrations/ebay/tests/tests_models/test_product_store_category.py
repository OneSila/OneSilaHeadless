from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.ebay.models import (
    EbayProductStoreCategory,
    EbaySalesChannel,
    EbayStoreCategory,
)


class EbayProductStoreCategoryModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.root = baker.make(
            EbayStoreCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="10",
            name="Fashion",
            level=1,
            parent=None,
            is_leaf=False,
        )
        self.leaf = baker.make(
            EbayStoreCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="11",
            name="Shirts",
            level=2,
            parent=self.root,
            is_leaf=True,
        )

    def test_primary_store_category_must_be_leaf(self):
        with self.assertRaises(ValidationError) as exc:
            EbayProductStoreCategory.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                primary_store_category=self.root,
            )

        self.assertIn("primary_store_category", exc.exception.message_dict)

    def test_secondary_store_category_must_be_leaf(self):
        with self.assertRaises(ValidationError) as exc:
            EbayProductStoreCategory.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                primary_store_category=self.leaf,
                secondary_store_category=self.root,
            )

        self.assertIn("secondary_store_category", exc.exception.message_dict)

    def test_allows_only_one_mapping_per_product_per_sales_channel(self):
        another_leaf_same_channel = baker.make(
            EbayStoreCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="12",
            name="Accessories",
            level=2,
            parent=self.root,
            is_leaf=True,
        )

        EbayProductStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            primary_store_category=self.leaf,
        )

        with self.assertRaises(ValidationError) as exc:
            EbayProductStoreCategory.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                primary_store_category=another_leaf_same_channel,
            )

        self.assertIn("product", exc.exception.message_dict)
