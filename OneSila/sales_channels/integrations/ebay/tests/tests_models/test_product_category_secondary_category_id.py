from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbayProductCategory,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayProductCategorySecondaryCategoryIdModelTest(TestCase):
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
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            default_category_tree_id="0",
        )

    def test_allows_leaf_secondary_category_id(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="111",
            name="Leaf",
            full_name="Leaf Category",
            has_children=False,
        )

        mapping = EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="",
            secondary_category_id="111",
        )

        self.assertEqual(mapping.secondary_category_id, "111")

    def test_rejects_non_leaf_secondary_category_id(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="222",
            name="Parent",
            full_name="Parent Category",
            has_children=True,
        )

        with self.assertRaises(ValidationError) as exc:
            EbayProductCategory.objects.create(
                product=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
                multi_tenant_company=self.multi_tenant_company,
                remote_id="",
                secondary_category_id="222",
            )

        self.assertEqual(
            exc.exception.message_dict["secondary_category_id"],
            ["Only leaf eBay categories can be assigned."],
        )

    def test_rejects_unknown_secondary_category_id(self):
        with self.assertRaises(ValidationError) as exc:
            EbayProductCategory.objects.create(
                product=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
                multi_tenant_company=self.multi_tenant_company,
                remote_id="",
                secondary_category_id="999",
            )

        self.assertEqual(
            exc.exception.message_dict["secondary_category_id"],
            ["eBay category does not exist for the given remote ID."],
        )

    def test_rejects_same_primary_and_secondary_category_id(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="123",
            name="Leaf",
            full_name="Leaf Category",
            has_children=False,
        )

        with self.assertRaises(ValidationError) as exc:
            EbayProductCategory.objects.create(
                product=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
                multi_tenant_company=self.multi_tenant_company,
                remote_id="123",
                secondary_category_id=" 123 ",
            )

        self.assertEqual(
            exc.exception.message_dict["remote_id"],
            ["Primary and secondary eBay categories cannot be the same."],
        )
        self.assertEqual(
            exc.exception.message_dict["secondary_category_id"],
            ["Primary and secondary eBay categories cannot be the same."],
        )
