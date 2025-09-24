from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.tests import TestCase
from django.db import connection
from django.db.utils import ProgrammingError
from sales_channels.integrations.ebay.factories.category_nodes import EbayCategoryNodeSyncFactory
from sales_channels.integrations.ebay.factories.sales_channels import EbayCategorySuggestionFactory
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayCategoryNodeSyncFactoryTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        table_name = EbayCategory._meta.db_table
        create_statement = (
            "CREATE TABLE IF NOT EXISTS "
            f"{table_name} "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL, "
            "marketplace_default_tree_id VARCHAR(50) NOT NULL, "
            "remote_id VARCHAR(50) NOT NULL, "
            "name VARCHAR(512) NOT NULL)"
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_statement)
        except ProgrammingError:
            pass
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        table_name = EbayCategory._meta.db_table
        drop_statement = f"DROP TABLE IF EXISTS {table_name}"
        try:
            with connection.cursor() as cursor:
                cursor.execute(drop_statement)
        except ProgrammingError:
            pass
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="example",
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="GB",
            default_category_tree_id="3",
        )

    def _build_payload(self) -> dict[str, object]:
        return {
            "categoryTreeId": "3",
            "rootCategoryNode": {
                "category": {"categoryId": "0", "categoryName": "Root"},
                "categoryTreeNodeLevel": 0,
                "leafCategoryTreeNode": False,
                "childCategoryTreeNodes": [
                    {
                        "category": {"categoryId": "100", "categoryName": "Parent"},
                        "categoryTreeNodeLevel": 1,
                        "leafCategoryTreeNode": False,
                        "childCategoryTreeNodes": [
                            {
                                "category": {"categoryId": "200", "categoryName": "Leaf"},
                                "categoryTreeNodeLevel": 2,
                                "leafCategoryTreeNode": True,
                                "childCategoryTreeNodes": None,
                            }
                        ],
                    }
                ],
            },
        }

    @patch("sales_channels.integrations.ebay.factories.category_nodes.sync.GetEbayAPIMixin.get_api")
    def test_creates_leaf_nodes(self, mock_get_api: Mock) -> None:
        api = SimpleNamespace(
            commerce_taxonomy_get_category_tree=Mock(return_value=self._build_payload()),
        )
        mock_get_api.return_value = api

        fac = EbayCategoryNodeSyncFactory(view=self.view)
        fac.run()

        node = EbayCategory.objects.get(remote_id="200", marketplace_default_tree_id="3")
        self.assertEqual(node.name, "Leaf")

    @patch("sales_channels.integrations.ebay.factories.category_nodes.sync.GetEbayAPIMixin.get_api")
    def test_removes_stale_nodes(self, mock_get_api: Mock) -> None:
        existing = EbayCategory.objects.create(
            remote_id="999",
            marketplace_default_tree_id="3",
            name="Old",
        )
        self.addCleanup(lambda: existing.delete())

        api = SimpleNamespace(
            commerce_taxonomy_get_category_tree=Mock(return_value=self._build_payload()),
        )
        mock_get_api.return_value = api

        fac = EbayCategoryNodeSyncFactory(view=self.view)
        fac.run()

        self.assertFalse(
            EbayCategory.objects.filter(
                remote_id="999",
                marketplace_default_tree_id="3",
            ).exists()
        )
        self.assertTrue(
            EbayCategory.objects.filter(
                remote_id="200",
                marketplace_default_tree_id="3",
            ).exists()
        )

    @patch("sales_channels.integrations.ebay.factories.sales_channels.categories.GetEbayAPIMixin.get_api")
    def test_suggestion_factory_uses_cached_categories(self, mock_get_api: Mock) -> None:
        EbayCategory.objects.create(
            remote_id="100",
            marketplace_default_tree_id="3",
            name="Parent",
        )
        EbayCategory.objects.create(
            remote_id="200",
            marketplace_default_tree_id="3",
            name="Leaf",
        )

        factory = EbayCategorySuggestionFactory(view=self.view, query="")
        factory.run()

        mock_get_api.assert_not_called()
        self.assertEqual(factory.category_tree_id, "3")
        self.assertEqual(
            factory.categories,
            [
                {
                    "category_id": "200",
                    "category_name": "Leaf",
                    "category_path": "Leaf",
                    "leaf": True,
                },
                {
                    "category_id": "100",
                    "category_name": "Parent",
                    "category_path": "Parent",
                    "leaf": True,
                },
            ],
        )
