from django.core.exceptions import ValidationError
from django.db import IntegrityError
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbayProductCategory,
    EbaySalesChannel,
    EbaySalesChannelView,
    EbayProductType,
)
from properties.models import Property


class EbayProductCategoryModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.product = baker.make(
            "products.Product",
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

    def test_str_contains_remote_id(self):
        mapping = EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="987654321",
        )

        self.assertIn("987654321", str(mapping))
        self.assertIn(str(self.product), str(mapping))
        self.assertIn(str(self.view), str(mapping))

    def test_unique_constraint_on_product_and_view(self):
        EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="123",
        )

        with self.assertRaises(IntegrityError):
            EbayProductCategory.objects.create(
                product=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
                multi_tenant_company=self.multi_tenant_company,
                remote_id="456",
            )


class EbayProductTypeModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.view = baker.make(
            EbaySalesChannelView,
            sales_channel=self.sales_channel,
            default_category_tree_id="0",
        )
        self.product_type_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_value = baker.make(
            "properties.PropertySelectValue",
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.rule = baker.make(
            "properties.ProductPropertiesRule",
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _create_product_type(self, **overrides):
        defaults = {
            "sales_channel": self.sales_channel,
            "marketplace": self.view,
            "local_instance": self.rule,
            "multi_tenant_company": self.multi_tenant_company,
        }
        defaults.update(overrides)
        return EbayProductType.objects.create(**defaults)

    def test_allows_leaf_remote_category(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="123",
            name="Leaf",
            full_name="Leaf Category",
            has_children=False,
        )

        product_type = self._create_product_type(remote_id="123")

        self.assertEqual(product_type.remote_id, "123")

    def test_rejects_non_leaf_remote_category(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="456",
            name="Parent",
            full_name="Parent Category",
            has_children=True,
        )

        with self.assertRaisesMessage(ValidationError, "Only leaf eBay categories can be assigned."):
            self._create_product_type(remote_id="456")

    def test_rejects_unknown_remote_category(self):
        with self.assertRaisesMessage(ValidationError, "eBay category does not exist for the given remote ID."):
            self._create_product_type(remote_id="999")

    def test_allows_leaf_remote_category(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="123",
            name="Leaf",
            full_name="Leaf Category",
            has_children=False,
        )

        mapping = EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="123",
        )

        self.assertEqual(mapping.remote_id, "123")

    def test_rejects_non_leaf_remote_category(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="456",
            name="Parent",
            full_name="Parent Category",
            has_children=True,
        )

        with self.assertRaisesMessage(ValidationError, "Only leaf eBay categories can be assigned."):
            EbayProductCategory.objects.create(
                product=self.product,
                sales_channel=self.sales_channel,
                view=self.view,
                multi_tenant_company=self.multi_tenant_company,
                remote_id="456",
            )
