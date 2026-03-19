from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductCategory,
    MiraklSalesChannel,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklCategoryModelTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )

    def test_category_cannot_reference_itself_as_parent(self):
        category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="leaf-1",
            name="Leaf",
        )
        category.parent = category

        with self.assertRaisesMessage(ValidationError, "Category cannot be its own parent."):
            category.full_clean()

    def test_product_category_requires_leaf_category(self):
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="parent-1",
            name="Parent",
            is_leaf=False,
        )

        with self.assertRaisesMessage(ValidationError, "Only leaf Mirakl categories can be assigned."):
            MiraklProductCategory.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                product=self.product,
                remote_id="parent-1",
            )

    def test_product_category_is_sales_channel_scoped(self):
        baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="leaf-2",
            name="Leaf",
            is_leaf=True,
        )

        mapping = MiraklProductCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            remote_id="leaf-2",
        )

        self.assertFalse(mapping.require_view)
        self.assertIsNone(mapping.view)
