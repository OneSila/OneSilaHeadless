from __future__ import annotations

from unittest.mock import MagicMock, patch

from model_bakery import baker

from products.product_types import CONFIGURABLE, SIMPLE
from sales_channels.integrations.ebay.factories.products.images import (
    EbayMediaProductThroughCreateFactory,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)


class EbayInventoryGroupPayloadTest(EbayProductPushFactoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.product.type = CONFIGURABLE
        self.product.save(update_fields=["type"])
        self.product.refresh_from_db()
        self.remote_product.refresh_from_db()

        self.child_one = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=SIMPLE,
            sku="CHILD-1",
        )

        self.child_two = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=SIMPLE,
            sku="CHILD-2",
        )

        baker.make(
            "products.ConfigurableVariation",
            multi_tenant_company=self.multi_tenant_company,
            parent=self.product,
            variation=self.child_one,
        )
        baker.make(
            "products.ConfigurableVariation",
            multi_tenant_company=self.multi_tenant_company,
            parent=self.product,
            variation=self.child_two,
        )

        assign = self._assign_remote(self.product, self.remote_product)
        assign.remote_id = "OFFER-PARENT"
        assign.save(update_fields=["remote_id"])

    def _assign_remote(self, product, remote_product):
        from sales_channels.models.sales_channels import SalesChannelViewAssign

        assign, _ = SalesChannelViewAssign.objects.get_or_create(
            product=product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            defaults={"remote_product": remote_product},
        )
        if assign.remote_product_id != remote_product.id:
            assign.remote_product = remote_product
            assign.save(update_fields=["remote_product"])
        return assign

    def _patch_variation_dimensions(self, values):
        return patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_variation_dimensions",
            return_value=values,
        )

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/img.jpg"],
    )
    def test_calls_group_api_for_configurable_parent(
        self,
        _mock_images,
    ):
        api = MagicMock()
        factory = EbayMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=False,
        )
        factory.log_action = MagicMock()
        factory.log_error = MagicMock()
        factory.api = api

        with self._patch_variation_dimensions([
            ("Color", "Red"),
            ("Color", "Blue"),
            ("Size", "Large"),
        ]):
            factory.create_remote()

        api.sell_inventory_create_or_replace_inventory_item.assert_not_called()
        api.sell_inventory_create_or_replace_inventory_item_group.assert_called_once()

        call_kwargs = api.sell_inventory_create_or_replace_inventory_item_group.call_args.kwargs
        self.assertEqual(call_kwargs["inventory_item_group_key"], self.product.sku)
        self.assertEqual(call_kwargs["content_language"], "en-us".replace("_", "-"))
        body = call_kwargs["body"]
        self.assertEqual(set(body.get("variant_skus", [])), {"CHILD-1", "CHILD-2"})
        varies_by = body.get("varies_by")
        self.assertEqual(sorted(varies_by.get("aspects_image_varies_by", [])), ["Color", "Size"])
        spec_map = {entry["name"]: entry["values"] for entry in varies_by.get("specifications", [])}
        self.assertEqual(sorted(spec_map["Color"]), ["Blue", "Red"])
        self.assertEqual(spec_map["Size"], ["Large"])
