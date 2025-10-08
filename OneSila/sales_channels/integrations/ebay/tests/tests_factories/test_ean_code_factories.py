from __future__ import annotations

from unittest.mock import MagicMock, patch

from model_bakery import baker

from eancodes.models import EanCode
from sales_channels.integrations.ebay.factories.products.eancodes import EbayEanCodeUpdateFactory
from sales_channels.integrations.ebay.models.products import EbayEanCode
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign


class EbayEanCodeUpdateFactoryTest(EbayProductPushFactoryTestBase):
    def _make_ean(self, *, code: str = "1234567890123") -> EanCode:
        return baker.make(
            "eancodes.EanCode",
            product=self.product,
            ean_code=code,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _build_factory(self, *, get_value_only: bool, remote_instance=None) -> EbayEanCodeUpdateFactory:
        return EbayEanCodeUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=get_value_only,
            remote_instance=remote_instance,
        )

    def test_preflight_requires_view_assignment(self):
        SalesChannelViewAssign.objects.filter(product=self.product).delete()

        factory = self._build_factory(get_value_only=False)
        result = factory.run()

        self.assertIsNone(result)
        self.assertFalse(
            EbayEanCode.objects.filter(remote_product=self.remote_product).exists()
        )

    @patch(
        "sales_channels.integrations.ebay.factories.products.eancodes.GetEbayAPIMixin.get_api",
        return_value=MagicMock(),
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=[],
    )
    def test_run_updates_remote_and_payload(
        self,
        _mock_collect_images,
        mock_get_api: MagicMock,
    ):
        self._make_ean(code="4006381333931")
        api = MagicMock()
        mock_get_api.return_value = api

        factory = self._build_factory(get_value_only=False)
        factory.run()

        remote_instance = factory.remote_instance
        remote_instance.refresh_from_db()
        self.assertEqual(remote_instance.ean_code, "4006381333931")

        api.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        payload = api.sell_inventory_create_or_replace_inventory_item.call_args.kwargs["body"]
        self.assertEqual(payload["product"]["ean"], "4006381333931")

    @patch(
        "sales_channels.integrations.ebay.factories.products.eancodes.GetEbayAPIMixin.get_api",
        return_value=MagicMock(),
    )
    def test_get_value_only_returns_ean_value_without_mutating_remote(
        self, _mock_get_api: MagicMock
    ):
        remote_instance = baker.make(
            "sales_channels.integrations.ebay.EbayEanCode",
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            ean_code="4006381333931",
        )
        self._make_ean(code="9501234567890")

        factory = self._build_factory(
            get_value_only=True,
            remote_instance=remote_instance,
        )
        value = factory.run()

        self.assertEqual(value, "9501234567890")
        remote_instance.refresh_from_db()
        self.assertEqual(remote_instance.ean_code, "4006381333931")
