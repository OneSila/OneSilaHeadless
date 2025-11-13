from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
)

from .queries import (
    SHEIN_CATEGORY_FILTER_BY_SITE_AND_LEAF,
    SHEIN_INTERNAL_PROPERTY_OPTION_FILTER_BY_INTERNAL_PROPERTY,
    SHEIN_PRODUCT_TYPE_FILTER_BY_CATEGORY,
    SHEIN_PRODUCT_TYPE_ITEM_FILTER_BY_PROPERTY,
    SHEIN_PROPERTY_FILTER_BY_SALES_CHANNEL,
    SHEIN_PROPERTY_SELECT_VALUE_FILTER_BY_PROPERTY,
)


class SheinPropertyQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="prop-1",
        )

    def test_filter_by_sales_channel(self):
        resp = self.strawberry_test_client(
            query=SHEIN_PROPERTY_FILTER_BY_SALES_CHANNEL,
            variables={"salesChannel": self.to_global_id(self.sales_channel)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinProperties"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.remote_property))


class SheinPropertySelectValueQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="prop-2",
        )
        self.remote_value = baker.make(
            SheinPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            remote_id="val-1",
        )

    def test_filter_by_property(self):
        resp = self.strawberry_test_client(
            query=SHEIN_PROPERTY_SELECT_VALUE_FILTER_BY_PROPERTY,
            variables={"property": self.to_global_id(self.remote_property)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinPropertySelectValues"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.remote_value))


class SheinProductTypeQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type = baker.make(
            SheinProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            category_id="category-1",
        )

    def test_filter_by_category(self):
        resp = self.strawberry_test_client(
            query=SHEIN_PRODUCT_TYPE_FILTER_BY_CATEGORY,
            variables={"categoryId": self.product_type.category_id},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinProductTypes"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.product_type))


class SheinProductTypeItemQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type = baker.make(
            SheinProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            category_id="category-2",
        )
        self.remote_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="prop-3",
        )
        self.product_type_item = baker.make(
            SheinProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=self.product_type,
            property=self.remote_property,
        )

    def test_filter_by_property(self):
        resp = self.strawberry_test_client(
            query=SHEIN_PRODUCT_TYPE_ITEM_FILTER_BY_PROPERTY,
            variables={"property": self.to_global_id(self.remote_property)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinProductTypeItems"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.product_type_item))


class SheinInternalPropertyOptionQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.internal_property = baker.make(
            SheinInternalProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="brand_code",
            name="Brand Code",
        )
        self.option = baker.make(
            SheinInternalPropertyOption,
            multi_tenant_company=self.multi_tenant_company,
            internal_property=self.internal_property,
            sales_channel=self.sales_channel,
            value="brand-1",
            label="Brand Option",
        )

    def test_filter_by_internal_property(self):
        resp = self.strawberry_test_client(
            query=SHEIN_INTERNAL_PROPERTY_OPTION_FILTER_BY_INTERNAL_PROPERTY,
            variables={"internalProperty": self.to_global_id(self.internal_property)},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinInternalPropertyOptions"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["node"]["id"], self.to_global_id(self.option))


class SheinCategoryQueryTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.root = baker.make(
            SheinCategory,
            remote_id="root-cat",
            site_remote_id="roe",
            is_leaf=False,
            parent=None,
            parent_remote_id="",
        )
        self.leaf = baker.make(
            SheinCategory,
            remote_id="leaf-cat",
            site_remote_id="roe",
            parent=self.root,
            parent_remote_id=self.root.remote_id,
            is_leaf=True,
        )

    def test_filter_by_site_and_leaf_flag(self):
        resp = self.strawberry_test_client(
            query=SHEIN_CATEGORY_FILTER_BY_SITE_AND_LEAF,
            variables={"siteRemoteId": self.root.site_remote_id},
        )
        self.assertTrue(resp.errors is None)
        edges = resp.data["sheinCategories"]["edges"]
        self.assertEqual(len(edges), 1)
        node = edges[0]["node"]
        self.assertEqual(node["id"], self.to_global_id(self.leaf))
        self.assertEqual(node["parentRemoteId"], self.root.remote_id)
