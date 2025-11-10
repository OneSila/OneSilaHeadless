from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.tests import TestCase
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from sales_channels.integrations.ebay.factories.category_nodes import EbayCategoryNodeSyncFactory
from sales_channels.integrations.ebay.factories.sales_channels import EbayCategorySuggestionFactory
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayCategoryNodeSyncFactoryTest(TestCase):

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

    def _build_aspects_payload(self) -> dict[str, object]:
        return {
            "aspects": [
                {
                    "localized_aspect_name": "Color",
                    "aspect_constraint": {"aspect_enabled_for_variations": True},
                },
                {
                    "localized_aspect_name": "Brand",
                    "aspect_constraint": {"aspect_enabled_for_variations": False},
                },
            ]
        }

    @patch("sales_channels.integrations.ebay.factories.category_nodes.sync.GetEbayAPIMixin.get_api")
    def test_creates_leaf_nodes(self, mock_get_api: Mock) -> None:
        api = SimpleNamespace(
            commerce_taxonomy_get_category_tree=Mock(return_value=self._build_payload()),
            commerce_taxonomy_get_item_aspects_for_category=Mock(return_value=self._build_aspects_payload()),
        )
        mock_get_api.return_value = api

        fac = EbayCategoryNodeSyncFactory(view=self.view)
        fac.run()

        node = EbayCategory.objects.get(remote_id="200", marketplace_default_tree_id="3")
        parent = EbayCategory.objects.get(remote_id="100", marketplace_default_tree_id="3")
        root = EbayCategory.objects.get(remote_id="0", marketplace_default_tree_id="3")

        self.assertEqual(node.full_name, "Root > Parent > Leaf")
        self.assertEqual(node.name, "Leaf")
        self.assertFalse(node.has_children)
        self.assertFalse(node.is_root)
        self.assertEqual(node.parent_node_id, parent.id)
        self.assertEqual(node.configurator_properties, ["Color"])

        self.assertEqual(parent.full_name, "Root > Parent")
        self.assertEqual(parent.name, "Parent")
        self.assertTrue(parent.has_children)
        self.assertFalse(parent.is_root)
        self.assertEqual(parent.parent_node_id, root.id)

        self.assertEqual(root.name, "Root")
        self.assertTrue(root.has_children)
        self.assertTrue(root.is_root)
        self.assertIsNone(root.parent_node)

    @patch("sales_channels.integrations.ebay.factories.category_nodes.sync.GetEbayAPIMixin.get_api")
    def test_removes_stale_nodes(self, mock_get_api: Mock) -> None:
        existing = EbayCategory.objects.create(
            remote_id="999",
            marketplace_default_tree_id="3",
            name="Old",
            full_name="Old",
        )
        self.addCleanup(lambda: existing.delete())

        api = SimpleNamespace(
            commerce_taxonomy_get_category_tree=Mock(return_value=self._build_payload()),
            commerce_taxonomy_get_item_aspects_for_category=Mock(return_value=self._build_aspects_payload()),
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
    def test_suggestion_factory_fetches_remote_suggestions(self, mock_get_api: Mock) -> None:
        payload = {
            "categoryTreeId": "3",
            "categorySuggestions": [
                {
                    "category": {"categoryId": "200", "categoryName": "Leaf"},
                    "categoryTreeNodeAncestors": [
                        {"category": {"categoryName": "Parent"}},
                    ],
                }
            ],
        }
        api = SimpleNamespace(
            commerce_taxonomy_get_category_suggestions=Mock(return_value=payload),
        )
        mock_get_api.return_value = api

        factory = EbayCategorySuggestionFactory(view=self.view, query=" Leaf ")
        factory.run()

        mock_get_api.assert_called_once_with()
        self.assertEqual(factory.category_tree_id, "3")
        self.assertEqual(
            factory.categories,
            [
                {
                    "category_id": "200",
                    "category_name": "Leaf",
                    "category_path": "Parent > Leaf",
                    "leaf": True,
                }
            ],
        )
