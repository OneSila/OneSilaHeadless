"""Tests for the Shein category tree synchronisation factory."""

from __future__ import annotations

from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.factories.sales_channels.full_schema import (
    SheinCategoryTreeSyncFactory,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductType,
    SheinSalesChannel,
    SheinSalesChannelView,
)


CATEGORY_TREE_PAYLOAD = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "category_id": 2028,
                "parent_category_id": 0,
                "category_name": "女士",
                "last_category": False,
                "children": [
                    {
                        "category_id": 2033,
                        "parent_category_id": 2028,
                        "category_name": "Clothing",
                        "last_category": False,
                        "children": [
                            {
                                "category_id": 1767,
                                "parent_category_id": 2033,
                                "category_name": "Dresses中文",
                                "last_category": False,
                                "children": [
                                    {
                                        "category_id": 1727,
                                        "product_type_id": 1080,
                                        "parent_category_id": 1767,
                                        "category_name": "Dresses/中文-四级",
                                        "last_category": True,
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    },
}


class SheinCategoryTreeFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            hostname="https://fr.shein.com",
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )
        self.view = baker.make(
            SheinSalesChannelView,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=True,
        )

    def test_run_creates_categories_and_product_types(self) -> None:
        response = Mock()
        response.json.return_value = CATEGORY_TREE_PAYLOAD

        factory = SheinCategoryTreeSyncFactory(sales_channel=self.sales_channel, view=self.view)

        with patch.object(SheinCategoryTreeSyncFactory, "shein_post", return_value=response) as mock_post:
            categories = factory.run()

        mock_post.assert_called_once()
        called_payload = mock_post.call_args.kwargs.get("payload")
        self.assertEqual(called_payload, {"site_abbr": self.view.remote_id})

        self.assertEqual(len(categories), SheinCategory.objects.count())
        self.assertEqual(SheinCategory.objects.count(), 4)
        self.assertEqual(
            SheinCategory.objects.filter(site_remote_id=self.view.remote_id).count(),
            4,
        )
        self.assertEqual(SheinProductType.objects.count(), 1)

        root_category = SheinCategory.objects.get(remote_id="2028")
        self.assertIsNone(root_category.parent)
        self.assertFalse(root_category.is_leaf)
        self.assertEqual(root_category.site_remote_id, self.view.remote_id)
        self.assertNotIn("children", root_category.raw_data)

        leaf_category = SheinCategory.objects.get(remote_id="1727")
        self.assertTrue(leaf_category.is_leaf)
        self.assertEqual(leaf_category.parent_remote_id, "1767")
        self.assertEqual(leaf_category.site_remote_id, self.view.remote_id)
        self.assertEqual(leaf_category.product_type_remote_id, "1080")

        product_type = SheinProductType.objects.get(remote_id="1080")
        self.assertEqual(product_type.category, leaf_category)
        self.assertTrue(product_type.is_leaf)
        self.assertEqual(product_type.name, leaf_category.name)
        self.assertEqual(product_type.view, self.view)
        self.assertNotIn("children", product_type.raw_data)
        self.assertIn(product_type, factory.synced_product_types)

    def test_run_uses_provided_tree_without_remote_call(self) -> None:
        tree = CATEGORY_TREE_PAYLOAD["info"]["data"]
        factory = SheinCategoryTreeSyncFactory(sales_channel=self.sales_channel, view=self.view)

        with patch.object(SheinCategoryTreeSyncFactory, "shein_post") as mock_post:
            categories = factory.run(tree=tree)

        mock_post.assert_not_called()
        self.assertEqual(SheinCategory.objects.count(), 4)
        self.assertEqual(len(categories), 4)
        self.assertEqual(SheinProductType.objects.count(), 1)
