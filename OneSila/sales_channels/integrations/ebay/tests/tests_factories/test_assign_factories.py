"""Tests for eBay assign factories."""

from __future__ import annotations

from typing import Dict
from unittest.mock import MagicMock, patch

from model_bakery import baker

from products.models import Product
from sales_channels.integrations.ebay.factories.products.assigns import (
    EbaySalesChannelViewAssignDeleteFactory,
    EbaySalesChannelViewAssignUpdateFactory,
)
from sales_channels.integrations.ebay.models import EbayProduct
from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)
from sales_channels.models import SalesChannelViewAssign


class _HelperSpec:
    def send_offer(self):  # pragma: no cover - interface placeholder
        raise NotImplementedError

    def publish_offer(self):  # pragma: no cover
        raise NotImplementedError

    def publish_group(self):  # pragma: no cover
        raise NotImplementedError

    def withdraw_offer(self):  # pragma: no cover
        raise NotImplementedError

    def withdraw_group(self):  # pragma: no cover
        raise NotImplementedError

    def delete_offer(self):  # pragma: no cover
        raise NotImplementedError


class EbayAssignFactoryTestBase(EbayProductPushFactoryTestBase):
    def setUp(self):
        super().setUp()
        self.additional_view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Germany",
            remote_id="EBAY_DE",
        )
        self.additional_assign = SalesChannelViewAssign.objects.create(
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.additional_view,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _stub_helpers(self, factory_cls) -> Dict[int, MagicMock]:
        helpers: Dict[int, MagicMock] = {}

        def helper_side_effect(factory_self, *, remote_product, **kwargs):
            helper = helpers.get(remote_product.id)
            if helper is None:
                helper = MagicMock(spec=_HelperSpec)
                helper.remote_product = remote_product
                helper.send_offer.return_value = {"offerId": f"OFFER-{remote_product.id}"}
                helper.publish_offer.return_value = {"status": "PUBLISHED"}
                helper.publish_group.return_value = {"status": "PUBLISHED_GROUP"}
                helper.withdraw_offer.return_value = {"status": "WITHDRAWN"}
                helper.withdraw_group.return_value = {"status": "WITHDRAWN_GROUP"}
                helper.delete_offer.return_value = {"status": "DELETED"}
                helpers[remote_product.id] = helper
            return helper

        patcher = patch.object(factory_cls, "_build_offer_helper", side_effect=helper_side_effect, autospec=True)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return helpers


class EbayAssignFactoryTests(EbayAssignFactoryTestBase):
    def test_update_simple_creates_offer_and_publishes(self):
        helpers = self._stub_helpers(EbaySalesChannelViewAssignUpdateFactory)

        with patch.object(EbaySalesChannelViewAssignUpdateFactory, "get_api", return_value=MagicMock()):
            factory = EbaySalesChannelViewAssignUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.additional_view,
            )
            factory.run()

        self.additional_assign.refresh_from_db()
        self.assertEqual(self.additional_assign.remote_product_id, self.remote_product.id)

        parent_helper = helpers[self.remote_product.id]
        parent_helper.send_offer.assert_called_once()
        parent_helper.publish_offer.assert_called_once()
        parent_helper.publish_group.assert_not_called()

    def test_update_configurable_creates_child_offers_and_publishes_group(self):
        self.product.type = Product.CONFIGURABLE
        self.product.save(update_fields=["type"])

        child_one = baker.make(
            "products.Product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        child_two = baker.make(
            "products.Product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        child_remote_one = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_one,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD-1",
            is_variation=True,
        )
        child_remote_two = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_two,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD-2",
            is_variation=True,
        )

        helpers = self._stub_helpers(EbaySalesChannelViewAssignUpdateFactory)

        with patch.object(EbaySalesChannelViewAssignUpdateFactory, "get_api", return_value=MagicMock()):
            factory = EbaySalesChannelViewAssignUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.additional_view,
            )
            factory.run()

        parent_helper = helpers[self.remote_product.id]
        parent_helper.send_offer.assert_not_called()
        parent_helper.publish_group.assert_called_once()

        child_helper_one = helpers[child_remote_one.id]
        child_helper_two = helpers[child_remote_two.id]
        child_helper_one.send_offer.assert_called_once()
        child_helper_two.send_offer.assert_called_once()
        child_helper_one.publish_offer.assert_not_called()
        child_helper_two.publish_offer.assert_not_called()

    def test_delete_simple_withdraws_and_deletes_offer(self):
        helpers = self._stub_helpers(EbaySalesChannelViewAssignDeleteFactory)

        with patch.object(EbaySalesChannelViewAssignDeleteFactory, "get_api", return_value=MagicMock()):
            factory = EbaySalesChannelViewAssignDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            factory.run()

        parent_helper = helpers[self.remote_product.id]
        parent_helper.withdraw_offer.assert_called_once()
        parent_helper.delete_offer.assert_called_once()
        parent_helper.withdraw_group.assert_not_called()

    def test_delete_configurable_withdraws_group_and_child_offers(self):
        self.product.type = Product.CONFIGURABLE
        self.product.save(update_fields=["type"])

        child_one = baker.make(
            "products.Product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        child_two = baker.make(
            "products.Product",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        child_remote_one = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_one,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD-1",
            is_variation=True,
        )
        child_remote_two = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_two,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD-2",
            is_variation=True,
        )

        helpers = self._stub_helpers(EbaySalesChannelViewAssignDeleteFactory)

        with patch.object(EbaySalesChannelViewAssignDeleteFactory, "get_api", return_value=MagicMock()):
            factory = EbaySalesChannelViewAssignDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            factory.run()

        parent_helper = helpers[self.remote_product.id]
        parent_helper.withdraw_group.assert_called_once()
        parent_helper.withdraw_offer.assert_called_once()
        parent_helper.delete_offer.assert_called_once()

        child_helper_one = helpers[child_remote_one.id]
        child_helper_two = helpers[child_remote_two.id]
        child_helper_one.withdraw_offer.assert_called_once()
        child_helper_two.withdraw_offer.assert_called_once()
        child_helper_one.delete_offer.assert_called_once()
        child_helper_two.delete_offer.assert_called_once()
