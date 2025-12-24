"""Tests for the Shein category suggestion factory."""

from __future__ import annotations

from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker
from media.models import Image

from sales_channels.integrations.shein.factories.sales_channels.categories import (
    SheinCategorySuggestionFactory,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinSalesChannel,
    SheinSalesChannelView,
)


SUGGESTION_PAYLOAD = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {"categoryId": "300", "order": 1, "vote": 8},
            {"categoryId": "999", "order": 2, "vote": 3},
        ],
    },
}


class SheinCategorySuggestionFactoryTests(TestCase):
    """Exercise different behaviours of the suggestion factory."""

    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )
        self.view = baker.make(
            SheinSalesChannelView,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
        )
        self.root = baker.make(
            SheinCategory,
            remote_id="100",
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Root",
            parent=None,
            parent_remote_id="",
            is_leaf=False,
        )
        self.child = baker.make(
            SheinCategory,
            remote_id="200",
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Child",
            parent=self.root,
            parent_remote_id=self.root.remote_id,
            is_leaf=False,
        )
        self.leaf = baker.make(
            SheinCategory,
            remote_id="300",
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Leaf",
            parent=self.child,
            parent_remote_id=self.child.remote_id,
            is_leaf=True,
            product_type_remote_id="1080",
        )

    def test_run_returns_normalized_entries_with_local_metadata(self) -> None:
        factory = SheinCategorySuggestionFactory(
            view=self.view,
            query=" Dresses ",
            image_url=" https://example.com/image.jpg ",
        )

        response = Mock()
        response.json.return_value = SUGGESTION_PAYLOAD

        with patch.object(SheinCategorySuggestionFactory, "shein_post", return_value=response) as mock_post:
            factory.run()

        self.assertTrue(mock_post.called)
        self.assertEqual(
            mock_post.call_args.kwargs["payload"],
            {
                "productInfo": "Dresses",
                "url": "https://example.com/image.jpg",
            },
        )
        self.assertEqual(len(factory.categories), 2)
        first = factory.categories[0]
        self.assertEqual(first["category_id"], "300")
        self.assertEqual(first["product_type_id"], "1080")
        self.assertEqual(first["category_name"], "Leaf")
        self.assertEqual(first["category_path"], "Root > Child > Leaf")
        self.assertTrue(first["leaf"])
        self.assertEqual(first["order"], 1)
        self.assertEqual(first["vote"], 8)
        second = factory.categories[1]
        self.assertEqual(second["category_name"], "")
        self.assertEqual(second["category_path"], "")
        self.assertFalse(second["leaf"])
        self.assertEqual(second["product_type_id"], "")

    def test_run_skips_api_call_without_payload(self) -> None:
        factory = SheinCategorySuggestionFactory(view=self.view, query="  ")
        with patch.object(SheinCategorySuggestionFactory, "shein_post") as mock_post:
            factory.run()
        mock_post.assert_not_called()
        self.assertEqual(factory.categories, [])

    def test_run_uses_image_object_url_when_available(self) -> None:
        image = Mock(spec=Image)
        image.image_url.return_value = "https://static.example.com/from-image"
        factory = SheinCategorySuggestionFactory(view=self.view, image=image)

        response = Mock()
        response.json.return_value = SUGGESTION_PAYLOAD

        with patch.object(SheinCategorySuggestionFactory, "shein_post", return_value=response) as mock_post:
            factory.run()

        self.assertEqual(
            mock_post.call_args.kwargs["payload"],
            {"url": "https://static.example.com/from-image"},
        )
